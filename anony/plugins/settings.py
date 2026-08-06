# Copyright (c) 2025 TygarX
# Licensed under the MIT License.
# This file is part of TygarXmusic

from pyrogram import filters, types

from anony import app, db, lang
from anony.helpers._admins import admin_check


def render(settings: dict) -> str:
    return (
        "<b>TygarXmusic settings</b>\n\n"
        f"Queue limit: <code>{settings['queue_limit']}</code>\n"
        f"Duration limit: <code>{settings['duration_limit']} min</code>\n"
        f"Video playback: <code>{'on' if settings['video_play'] else 'off'}</code>\n"
        f"Thumbnail generation: <code>{'on' if settings['thumb_gen'] else 'off'}</code>\n"
        f"Radio mode: <code>{'on' if settings['radio_mode'] else 'off'}</code>\n\n"
        "Use /settings key value, for example: /settings queue_limit 30"
    )


@app.on_message(filters.command("settings") & filters.group & ~app.bl_users)
@lang.language()
@admin_check
async def settings_handler(_, m: types.Message):
    settings = await db.get_settings(m.chat.id)
    if len(m.command) == 1:
        return await m.reply_text(render(settings))
    if len(m.command) != 3:
        return await m.reply_text(
            "Usage: /settings <queue_limit|duration_limit|video_play|thumb_gen|radio_mode> <value>"
        )
    key, raw = m.command[1], m.command[2].lower()
    try:
        value = (
            int(raw)
            if key in {"queue_limit", "duration_limit"}
            else raw in {"1", "true", "on", "yes"}
        )
        settings = await db.set_setting(m.chat.id, key, value)
    except (ValueError, TypeError):
        return await m.reply_text("Invalid setting or value.")
    await m.reply_text(render(settings))
