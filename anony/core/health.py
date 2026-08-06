"""Small health and readiness HTTP service for container orchestration."""

import asyncio
from contextlib import suppress

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

from anony import config, db, logger

app = FastAPI(title="TygarXmusic health", docs_url=None, redoc_url=None)
_started = False
_server_task: asyncio.Task | None = None


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "tygarxmusic"}


@app.get("/readyz")
async def readyz():
    if not _started:
        return JSONResponse({"status": "starting"}, status_code=503)
    try:
        await db.mongo.admin.command("ping")
    except Exception:
        return JSONResponse({"status": "not_ready"}, status_code=503)
    return {"status": "ready"}


async def start() -> None:
    global _started, _server_task
    if _server_task:
        return
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=config.HEALTH_HOST,
            port=config.HEALTH_PORT,
            log_config=None,
            access_log=False,
        )
    )
    _server_task = asyncio.create_task(server.serve())
    _started = True
    logger.info("health_server_started", extra={"port": config.HEALTH_PORT})


async def stop() -> None:
    global _server_task, _started
    if not _server_task:
        return
    _server_task.cancel()
    with suppress(asyncio.CancelledError):
        await _server_task
    _server_task = None
    _started = False
