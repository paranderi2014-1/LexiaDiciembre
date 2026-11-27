"""Carga manual de fuentes oficiales (§8, §9).

    python -m scripts.load_sources bacn --limite 5
    python -m scripts.load_sources todas
"""

from __future__ import annotations

import argparse
import asyncio
import json

from app.database.session import SessionLocal
from app.jobs.actualizacion import actualizar_todo
from app.jobs.etl import run_source
from app.scrapers.portals import SCRAPERS


async def _run(fuente: str, limite: int | None) -> dict:
    async with SessionLocal() as session:
        if fuente == "todas":
            return await actualizar_todo(session, limite_por_fuente=limite)
        report = await run_source(session, fuente, limite=limite)
        return report.as_dict()


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga documentos jurídicos oficiales")
    parser.add_argument("fuente", choices=[*SCRAPERS, "todas"], help="portal a procesar")
    parser.add_argument("--limite", type=int, default=None, help="máximo de documentos")
    args = parser.parse_args()

    resultado = asyncio.run(_run(args.fuente, args.limite))
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
