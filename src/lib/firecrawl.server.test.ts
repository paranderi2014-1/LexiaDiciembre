import { describe, expect, it } from "vitest";
import { isAllowedLegalUrl } from "./firecrawl.server";

describe("fuentes jurídicas autorizadas para Firecrawl", () => {
  it("acepta los dominios oficiales paraguayos", () => {
    expect(isAllowedLegalUrl("https://www.bacn.gov.py/leyes-paraguayas")).toBe(true);
    expect(isAllowedLegalUrl("https://www.pj.gov.py/")).toBe(true);
    expect(isAllowedLegalUrl("https://www.csj.gov.py/jurisprudencia/")).toBe(true);
    expect(isAllowedLegalUrl("https://apps.csj.gov.py/login")).toBe(true);
  });
  it("rechaza dominios parecidos, HTTP y hosts externos", () => {
    expect(isAllowedLegalUrl("https://bacn.gov.py.evil.example/")).toBe(false);
    expect(isAllowedLegalUrl("http://www.bacn.gov.py/")).toBe(false);
    expect(isAllowedLegalUrl("https://example.com/" )).toBe(false);
    expect(isAllowedLegalUrl("not a url")).toBe(false);
  });
});
