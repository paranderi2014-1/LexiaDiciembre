import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";
import { searchParaguayLegal, scrapeParaguayLegal } from "@/lib/firecrawl.server";

const CURRENT_PROTOCOL = "2026-07-28";
const LEGACY_PROTOCOLS = ["2025-11-25", "2025-06-18", "2025-03-26"];
const SUPPORTED_PROTOCOLS = [CURRENT_PROTOCOL, ...LEGACY_PROTOCOLS];
const rpcRequest = z.object({
  jsonrpc: z.literal("2.0"),
  id: z.union([z.string(), z.number(), z.null()]).optional(),
  method: z.string(),
  params: z.record(z.string(), z.unknown()).optional(),
});
const tools = [
  {
    name: "paraguay_legal_search",
    description: "Busca legislación, jurisprudencia y contenido jurídico en fuentes oficiales paraguayas BACN, Poder Judicial y CSJ usando Firecrawl.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", minLength: 3, maxLength: 500 },
        limit: { type: "integer", minimum: 1, maximum: 10 },
      },
      required: ["query"],
      additionalProperties: false,
    },
  },
  {
    name: "paraguay_legal_scrape",
    description: "Extrae el contenido de una URL oficial paraguaya de BACN, Poder Judicial o CSJ.",
    inputSchema: {
      type: "object",
      properties: { url: { type: "string", format: "uri" } },
      required: ["url"],
      additionalProperties: false,
    },
  },
];

function responseHeaders(version: string) {
  return { "Cache-Control": "no-store", "MCP-Protocol-Version": version };
}
function jsonRpc(id: string | number | null | undefined, result: unknown, version: string) {
  return Response.json({ jsonrpc: "2.0", id: id ?? null, result }, { headers: responseHeaders(version) });
}
function jsonRpcError(id: string | number | null | undefined, code: number, message: string, version: string, status = 400) {
  return Response.json({ jsonrpc: "2.0", id: id ?? null, error: { code, message } }, { status, headers: responseHeaders(version) });
}

export const Route = createFileRoute("/api/mcp")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const expected = process.env["MCP_ACCESS_TOKEN"];
        const authorization = request.headers.get("authorization") ?? "";
        if (!expected || !authorization.startsWith("Bearer ") || authorization.slice(7) !== expected) {
          return Response.json({ error: "Unauthorized" }, { status: 401, headers: { "WWW-Authenticate": "Bearer" } });
        }

        const origin = request.headers.get("origin");
        if (origin) {
          const configured = (process.env["MCP_ALLOWED_ORIGINS"] ?? "").split(",").map((value) => value.trim()).filter(Boolean);
          const allowed = new Set([new URL(request.url).origin, ...configured]);
          if (!allowed.has(origin)) return Response.json({ error: "Origin not allowed" }, { status: 403 });
        }

        const accept = request.headers.get("accept") ?? "";
        if (!accept.includes("application/json") || !accept.includes("text/event-stream")) {
          return Response.json({ error: "Accept must include application/json and text/event-stream." }, { status: 406 });
        }
        if (!request.headers.get("content-type")?.toLowerCase().includes("application/json")) {
          return Response.json({ error: "Content-Type must be application/json." }, { status: 415 });
        }

        const parsed = rpcRequest.safeParse(await request.json().catch(() => null));
        if (!parsed.success) return jsonRpcError(null, -32700, "Invalid JSON-RPC request", CURRENT_PROTOCOL);
        const { id, method, params = {} } = parsed.data;
        const requestedVersion = request.headers.get("MCP-Protocol-Version") || LEGACY_PROTOCOLS[2]!;
        if (!SUPPORTED_PROTOCOLS.includes(requestedVersion)) {
          return jsonRpcError(id, -32000, `Unsupported protocol version. Supported: ${SUPPORTED_PROTOCOLS.join(", ")}`, CURRENT_PROTOCOL);
        }

        if (requestedVersion === CURRENT_PROTOCOL) {
          const meta = params["_meta"];
          const metaVersion = typeof meta === "object" && meta !== null
            ? (meta as Record<string, unknown>)["io.modelcontextprotocol/protocolVersion"]
            : undefined;
          const methodHeader = request.headers.get("Mcp-Method");
          const toolName = typeof params["name"] === "string" ? params["name"] : "";
          const nameHeader = request.headers.get("Mcp-Name");
          if (metaVersion !== requestedVersion || methodHeader !== method || (method === "tools/call" && nameHeader !== toolName)) {
            return jsonRpcError(id, -32020, "MCP request headers do not match the JSON-RPC body.", CURRENT_PROTOCOL);
          }
        }

        if (method === "notifications/initialized") return new Response(null, { status: 202, headers: responseHeaders(requestedVersion) });
        if (method === "initialize") {
          const requested = typeof params["protocolVersion"] === "string" ? params["protocolVersion"] : requestedVersion;
          const negotiated = SUPPORTED_PROTOCOLS.includes(requested) ? requested : LEGACY_PROTOCOLS[0]!;
          return jsonRpc(id, { protocolVersion: negotiated, capabilities: { tools: {} }, serverInfo: { name: "lexia-paraguay-mcp", version: "1.0.0" } }, negotiated);
        }
        if (method === "ping") return jsonRpc(id, {}, requestedVersion);
        if (method === "tools/list") return jsonRpc(id, { tools }, requestedVersion);
        if (method === "tools/call") {
          const name = typeof params["name"] === "string" ? params["name"] : "";
          const args = params["arguments"] ?? {};
          try {
            const result = name === "paraguay_legal_search"
              ? await searchParaguayLegal(args)
              : name === "paraguay_legal_scrape"
                ? await scrapeParaguayLegal(args)
                : null;
            if (!result) return jsonRpcError(id, -32602, "Unknown tool", requestedVersion);
            return jsonRpc(id, { content: [{ type: "text", text: JSON.stringify(result) }], structuredContent: result, isError: false }, requestedVersion);
          } catch (error) {
            const message = error instanceof Error ? error.message : "Tool execution failed";
            return jsonRpc(id, { content: [{ type: "text", text: message }], isError: true }, requestedVersion);
          }
        }
        return jsonRpcError(id, -32601, "Method not found", requestedVersion, 404);
      },
      GET: async () => new Response("MCP endpoint accepts authenticated POST requests only.", { status: 405, headers: { Allow: "POST" } }),
    },
  },
});
