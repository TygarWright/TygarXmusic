"""Small health and readiness HTTP service for container orchestration."""

import asyncio
from contextlib import suppress

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
from pathlib import Path

from anony import config, db, logger

app = FastAPI(title="TygarXmusic health", docs_url=None, redoc_url=None)
_started = False
_server_task: asyncio.Task | None = None


@app.get("/dashboard")
async def dashboard():
    return FileResponse(Path("dashboard/index.html"))


@app.get("/dashboard/{asset:path}")
async def dashboard_asset(asset: str):
    path = Path("dashboard") / asset
    if not path.is_file() or ".." in path.parts:
        return JSONResponse({"error": "not_found"}, status_code=404)
    return FileResponse(path)


@app.get("/metrics")
async def metrics():
    from anony import boot, db

    uptime = int(asyncio.get_running_loop().time() - boot)
    return {
        "uptime": f"{uptime // 3600}h {(uptime % 3600) // 60}m",
        "active_calls": len(db.active_calls),
        "known_chats": len(db.chats),
        "known_users": len(db.users),
        "queue_items": sum(len(q) for q in __import__("anony").queue.queues.values()),
    }


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
