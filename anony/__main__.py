# Copyright (c) 2025 TygarX
# Licensed under the MIT License.
# This file is part of TygarXmusic


import asyncio
import importlib
import signal
from contextlib import suppress

from anony import anon, app, config, db, logger, queue, stop, thumb, userbot, yt
from anony.core import health
from anony.plugins import all_modules


async def idle():
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGABRT):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)
    await stop_event.wait()


async def main():
    config.check()
    await db.connect()
    await health.start()
    await app.boot()
    await userbot.boot()
    await anon.boot()
    await thumb.start()

    for module in all_modules:
        importlib.import_module(f"anony.plugins.{module}")
    logger.info(f"Loaded {len(all_modules)} modules.")

    if config.COOKIES_URL:
        await yt.save_cookies(config.COOKIES_URL)

    sudoers = await db.get_sudoers()
    app.sudoers.update(sudoers)
    app.bl_users.update(await db.get_blacklisted())
    logger.info(f"Loaded {len(app.sudoers)} sudo users.")
    for chat_id in await db.get_chats():
        saved = await db.load_queue(chat_id)
        if saved:
            queue.restore(chat_id, saved)
            logger.info(
                "queue_recovered", extra={"chat_id": chat_id, "items": len(saved)}
            )

    await idle()
    await health.stop()
    asyncio.create_task(stop())


if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        pass
