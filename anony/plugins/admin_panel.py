# Copyright (c) 2025 TygarX
# Licensed under the MIT License.
# This file is part of TygarXmusic


from pyrogram import filters, types

from anony import app, db

# ─────────────────────────── helpers ────────────────────────────


def _e(v: bool) -> str:
    return "✅ ON" if v else "❌ OFF"


def _panel_text(p: dict) -> str:
    fsub_ch = f"@{p['fsub_username']}" if p.get("fsub_username") else "not set"
    return (
        "<u><b>🛠 TygarX Admin Panel</b></u>\n\n"
        f"<b>🔒 Force Subscribe:</b>  {_e(p['fsub'])}\n"
        f"   └ Channel: <code>{fsub_ch}</code>\n\n"
        f"<b>🔧 Maintenance Mode:</b>  {_e(p['maintenance'])}\n"
        f"   └ Blocks all non-admin users from playing\n\n"
        f"<b>⏱ Duration Limit:</b>  <code>{p['duration_limit']} min</code>\n"
        f"   └ Songs longer than this won't play\n\n"
        f"<b>📋 Queue Limit:</b>  <code>{p['queue_limit']} tracks</code>\n"
        f"   └ Max songs allowed in queue per group\n\n"
        f"<b>🖼 Thumbnails:</b>  {_e(p['thumb_gen'])}\n"
        f"<b>📹 Video Play:</b>  {_e(p['video_play'])}\n\n"
        "<i>To set the force-subscribe channel: /setfsub @yourchannel\n"
        "The bot must be an admin in that channel.</i>"
    )


def _panel_markup(p: dict) -> types.InlineKeyboardMarkup:
    ikb = types.InlineKeyboardButton
    dur = p["duration_limit"]
    que = p["queue_limit"]

    return types.InlineKeyboardMarkup(
        [
            # Force subscribe toggle
            [
                ikb(
                    f"🔒 Force Subscribe: {_e(p['fsub'])}",
                    callback_data="panel_tog fsub",
                )
            ],
            # Maintenance toggle
            [
                ikb(
                    f"🔧 Maintenance: {_e(p['maintenance'])}",
                    callback_data="panel_tog maintenance",
                )
            ],
            # Duration limit with +/- controls (step: 15 min)
            [
                ikb("⏱ Duration", callback_data="panel_noop"),
                ikb("➖", callback_data="panel_dur -"),
                ikb(f"{dur} min", callback_data="panel_noop"),
                ikb("➕", callback_data="panel_dur +"),
            ],
            # Queue limit with +/- controls (step: 5 tracks)
            [
                ikb("📋 Queue", callback_data="panel_noop"),
                ikb("➖", callback_data="panel_que -"),
                ikb(f"{que} tracks", callback_data="panel_noop"),
                ikb("➕", callback_data="panel_que +"),
            ],
            # Thumbnails and video toggles on one row
            [
                ikb(
                    f"🖼 Thumbnails: {_e(p['thumb_gen'])}",
                    callback_data="panel_tog thumb",
                ),
                ikb(
                    f"📹 Video: {_e(p['video_play'])}", callback_data="panel_tog video"
                ),
            ],
            [ikb("✖ Close", callback_data="panel_close")],
        ]
    )


# ─────────────────────────── commands ───────────────────────────


@app.on_message(filters.command(["panel", "adminpanel"]) & app.sudoers)
async def _panel(_, m: types.Message):
    p = await db.get_panel()
    await m.reply_text(_panel_text(p), reply_markup=_panel_markup(p))


@app.on_message(filters.command(["setfsub"]) & app.sudoers)
async def _setfsub(_, m: types.Message):
    if len(m.command) < 2:
        return await m.reply_text(
            "<b>Usage:</b> <code>/setfsub @yourchannel</code>\n\n"
            "The bot must be an <b>admin</b> in the channel so it can verify members.\n"
            "After setting the channel, enable force subscribe from /panel."
        )

    channel = m.command[1].lstrip("@")
    try:
        chat = await app.get_chat(channel)
        ch_username = chat.username or channel
        await db.set_panel("fsub_id", chat.id)
        await db.set_panel("fsub_username", ch_username)
        await m.reply_text(
            f"✅ Force subscribe channel set to <b>@{ch_username}</b>.\n\n"
            f"Now go to /panel and enable <b>Force Subscribe</b>."
        )
    except Exception as ex:
        await m.reply_text(
            f"❌ Couldn't find that channel.\n\n"
            f"Make sure the bot is an <b>admin</b> in the channel and the username is correct.\n\n"
            f"<code>{type(ex).__name__}: {ex}</code>"
        )


# ─────────────────────────── callbacks ──────────────────────────


@app.on_callback_query(filters.regex(r"^panel") & app.sudoers)
async def _panel_cb(_, query: types.CallbackQuery):
    parts = query.data.split()
    action = parts[1] if len(parts) > 1 else None

    # Info-only buttons — just dismiss the tap
    if action == "noop":
        return await query.answer()

    # Close button — delete the panel message
    if action == "close":
        await query.answer()
        return await query.message.delete()

    p = await db.get_panel()

    if action == "tog":
        # Map short key → actual panel dict key
        key_map = {
            "fsub": "fsub",
            "maintenance": "maintenance",
            "thumb": "thumb_gen",
            "video": "video_play",
        }
        short_key = parts[2] if len(parts) > 2 else None
        db_key = key_map.get(short_key)

        if not db_key:
            return await query.answer("Unknown setting.", show_alert=True)

        # Guard: can't enable force subscribe without a channel set
        if short_key == "fsub" and not p.get("fsub_id") and not p.get("fsub"):
            return await query.answer(
                "⚠️ Set a channel first!\nRun: /setfsub @yourchannel",
                show_alert=True,
            )

        new_val = not p[db_key]
        await db.set_panel(db_key, new_val)
        p[db_key] = new_val
        await query.answer("Enabled ✅" if new_val else "Disabled ❌")

    elif action == "dur":
        direction = parts[2] if len(parts) > 2 else "+"
        cur = p["duration_limit"]
        new_val = cur + (15 if direction == "+" else -15)

        if new_val < 15:
            return await query.answer("Minimum is 15 min.", show_alert=True)
        if new_val > 360:
            return await query.answer("Maximum is 360 min (6 h).", show_alert=True)

        await db.set_panel("duration_limit", new_val)
        p["duration_limit"] = new_val
        await query.answer(f"Duration limit: {new_val} min")

    elif action == "que":
        direction = parts[2] if len(parts) > 2 else "+"
        cur = p["queue_limit"]
        new_val = cur + (5 if direction == "+" else -5)

        if new_val < 5:
            return await query.answer("Minimum is 5 tracks.", show_alert=True)
        if new_val > 50:
            return await query.answer("Maximum is 50 tracks.", show_alert=True)

        await db.set_panel("queue_limit", new_val)
        p["queue_limit"] = new_val
        await query.answer(f"Queue limit: {new_val} tracks")

    # Refresh the panel message with updated values
    try:
        await query.edit_message_text(_panel_text(p), reply_markup=_panel_markup(p))
    except Exception:
        pass
