"""Planificador diario de actualización (§19).

Uso:
    python -m app.jobs.scheduler           # queda escuchando (03:00 America/Asuncion)
    python -m app.jobs.scheduler --once    # ejecuta una actualización y sale
"""

from __future__ import annotations

import argparse
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.database.session import SessionLocal
from app.jobs.actualizacion import actualizar_todo


async def ejecutar_una_vez() -> dict:
    async with SessionLocal() as session:
        return await actualizar_todo(session)


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.update_timezone)
    scheduler.add_job(
        ejecutar_una_vez,
        CronTrigger(
            hour=settings.update_hour,
            minute=settings.update_minute,
            timezone=settings.update_timezone,
        ),
        id="actualizacion-diaria",
        replace_existing=True,
    )
    return scheduler


def main() -> None:
    parser = argparse.ArgumentParser(description="Actualización automática de fuentes oficiales")
    parser.add_argument("--once", action="store_true", help="ejecutar una vez y salir")
    args = parser.parse_args()

    if args.once:
        asyncio.run(ejecutar_una_vez())
        return

    asyncio.run(_serve())


async def _serve() -> None:
    scheduler = build_scheduler()
    scheduler.start()
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()
