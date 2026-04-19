"""
╔══════════════════════════════════════════════════════════════╗
║            JOIN REQUEST BOT — bot.py                        ║
║                                                              ║
║  ✅ 1 se 10 bots ek saath ek file se                        ║
║  ✅ Join request pe auto DM (bina START ke)                  ║
║  ✅ Auto Approve ON/OFF (per bot)                            ║
║  ✅ Custom message: Text / Image+Text / Video+Text           ║
║  ✅ Inline buttons with label + URL                          ║
║  ✅ Preview + Publish                                        ║
║  ✅ /broadcast — text/photo/video + inline buttons           ║
║  ✅ Users auto-register (broadcast ke liye)                  ║
║  ✅ Real-time broadcast progress report                      ║
║                                                              ║
║  ⚙️  Sirf config.py edit karo — yeh file mat chhuo          ║
╚══════════════════════════════════════════════════════════════╝

SETUP:
  1. pip install python-telegram-bot==20.7
  2. config.py mein tokens, OWNER_ID, ADMIN_IDS set karo
  3. python bot.py

BROADCAST:
  /start → 📡 Broadcast  ya  seedha /broadcast
  → Type choose karo (text / photo / video)
  → Content bhejo  (caption saath mein likh sakte ho)
  → Inline buttons add karo (optional)
  → Preview → Confirm → Send!
"""

import json, os, logging, asyncio, threading

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ChatJoinRequestHandler,
)
from telegram.constants import ParseMode
from telegram.error import Forbidden, BadRequest

import config as cfg

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════
#              💾 Settings helpers
# ════════════════════════════════════════════════

def load_settings(bk: str) -> dict:
    path = cfg.SETTINGS_FILES.get(bk)
    if path and os.path.exists(path):
        d = json.load(open(path, encoding="utf-8"))
        for k, v in cfg.DEFAULT_SETTINGS.items():
            d.setdefault(k, v)
        return d
    return cfg.DEFAULT_SETTINGS.copy()


def save_settings(bk: str, s: dict):
    json.dump(
        s,
        open(cfg.SETTINGS_FILES[bk], "w", encoding="utf-8"),
        indent=2,
        ensure_ascii=False,
    )


# ════════════════════════════════════════════════
#              👥 Users DB
# ════════════════════════════════════════════════

def load_users(bk: str) -> dict:
    path = cfg.USERS_FILES.get(bk)
    if path and os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return {}


def save_users(bk: str, u: dict):
    json.dump(
        u,
        open(cfg.USERS_FILES[bk], "w", encoding="utf-8"),
        indent=2,
        ensure_ascii=False,
    )


def add_user(bk: str, uid: int, first_name: str, username: str = ""):
    u = load_users(bk)
    u[str(uid)] = {"first_name": first_name, "username": username}
    save_users(bk, u)


# ════════════════════════════════════════════════
#              🔑 Auth
# ════════════════════════════════════════════════

def is_auth(uid: int) -> bool:
    return uid == cfg.OWNER_ID or uid in cfg.ADMIN_IDS


# ════════════════════════════════════════════════
#              📤 Send helper
# ════════════════════════════════════════════════

async def send_msg(
    bot, chat_id: int, mtype: str, text: str,
    media_id, buttons: list, name: str = ""
):
    if name:
        text = text.replace("{name}", name).replace("{first_name}", name)

    kb = (
        InlineKeyboardMarkup(
            [[InlineKeyboardButton(b["text"], url=b["url"])] for b in buttons]
        )
        if buttons
        else None
    )

    if mtype == "photo" and media_id:
        await bot.send_photo(
            chat_id=chat_id, photo=media_id,
            caption=text, parse_mode=ParseMode.HTML, reply_markup=kb,
        )
    elif mtype == "video" and media_id:
        await bot.send_video(
            chat_id=chat_id, video=media_id,
            caption=text, parse_mode=ParseMode.HTML, reply_markup=kb,
        )
    else:
        await bot.send_message(
            chat_id=chat_id, text=text,
            parse_mode=ParseMode.HTML, reply_markup=kb,
        )


# ════════════════════════════════════════════════
#              📡 Broadcast engine
# ════════════════════════════════════════════════

async def do_broadcast(
    bot, bk: str, label: str, admin_cid: int,
    mtype: str, text: str, media_id, buttons: list,
):
    users = load_users(bk)
    total = len(users)
    ok = fail = blocked = 0

    if total == 0:
        await bot.send_message(
            admin_cid,
            "⚠️ Abhi koi user registered nahi hai.\n"
            "Jab koi join request bhejega tab register hoga.",
        )
        return

    pm = await bot.send_message(
        admin_cid,
        f"📡 <b>Broadcast shuru...</b>\n\n"
        f"👥 Total: <b>{total}</b>\n✅ Sent: 0  ❌ Failed: 0",
        parse_mode=ParseMode.HTML,
    )

    for i, (uid_str, udata) in enumerate(users.items(), 1):
        try:
            await send_msg(
                bot, int(uid_str), mtype, text, media_id, buttons,
                name=udata.get("first_name", ""),
            )
            ok += 1
        except Forbidden:
            blocked += 1
            fail += 1
        except (BadRequest, Exception) as e:
            logger.warning(f"[{label}] BC fail {uid_str}: {e}")
            fail += 1

        if i % 20 == 0 or i == total:
            try:
                await pm.edit_text(
                    f"📡 <b>Broadcast chal raha hai...</b>\n\n"
                    f"👥 Total: <b>{total}</b>\n"
                    f"✅ Sent: <b>{ok}</b>  ❌ Failed: <b>{fail}</b>\n"
                    f"🚫 Blocked: <b>{blocked}</b>\n"
                    f"⏳ Progress: <b>{i}/{total}</b>",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass

        await asyncio.sleep(0.05)   # flood guard

    await bot.send_message(
        admin_cid,
        f"✅ <b>Broadcast Complete!</b>\n\n"
        f"👥 Total: <b>{total}</b>\n"
        f"✅ Sent: <b>{ok}</b>\n"
        f"❌ Failed: <b>{fail}</b>\n"
        f"🚫 Blocked/Deleted: <b>{blocked}</b>",
        parse_mode=ParseMode.HTML,
    )
    logger.info(f"[{label}] Broadcast done → {ok}/{total}")


# ════════════════════════════════════════════════
#              🎛️ Keyboards
# ════════════════════════════════════════════════

def kb_main(s: dict) -> InlineKeyboardMarkup:
    aa = "✅ ON" if s["auto_approve"] else "❌ OFF"
    mt = {"text": "📝 Text", "photo": "🖼️ Image", "video": "🎥 Video"}.get(
        s["message_type"], "📝"
    )
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🤖 Auto Approve: {aa}",        callback_data="toggle_approve")],
        [InlineKeyboardButton(f"✏️ Message Set Karo ({mt})",   callback_data="set_message")],
        [InlineKeyboardButton(f"🔘 Inline Buttons ({len(s['inline_buttons'])})", callback_data="manage_buttons")],
        [InlineKeyboardButton("👁️ Preview",  callback_data="preview"),
         InlineKeyboardButton("🚀 Publish",  callback_data="publish")],
        [InlineKeyboardButton("📡 Broadcast", callback_data="bc_menu"),
         InlineKeyboardButton("📊 Stats",     callback_data="stats")],
    ])


def kb_msg_type() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Sirf Text",    callback_data="mt_text"),
         InlineKeyboardButton("🖼️ Image+Text",  callback_data="mt_photo")],
        [InlineKeyboardButton("🎥 Video+Text",   callback_data="mt_video")],
        [InlineKeyboardButton("🔙 Back",         callback_data="back_main")],
    ])


def kb_btn_list(s: dict) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"❌ {b['text']}", callback_data=f"rm_btn_{i}")]
        for i, b in enumerate(s["inline_buttons"])
    ]
    rows += [
        [InlineKeyboardButton("➕ Naya Button Add Karo", callback_data="add_btn")],
        [InlineKeyboardButton("🔙 Back",                callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(rows)


def kb_after_save() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Button Add Karo", callback_data="manage_buttons")],
        [InlineKeyboardButton("👁️ Preview",        callback_data="preview")],
        [InlineKeyboardButton("🔙 Main Menu",       callback_data="back_main")],
    ])


def kb_after_btn() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Aur Button Add Karo", callback_data="add_btn")],
        [InlineKeyboardButton("👁️ Preview",            callback_data="preview")],
        [InlineKeyboardButton("🔙 Main Menu",           callback_data="back_main")],
    ])


# broadcast keyboards
def kb_bc_type() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Sirf Text",        callback_data="bc_t_text")],
        [InlineKeyboardButton("🖼️ Photo + Caption",  callback_data="bc_t_photo")],
        [InlineKeyboardButton("🎥 Video + Caption",  callback_data="bc_t_video")],
        [InlineKeyboardButton("🔙 Back",             callback_data="back_main")],
    ])


def kb_bc_after_content() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔘 Inline Button Add Karo", callback_data="bc_add_btn")],
        [InlineKeyboardButton("👁️ Preview",               callback_data="bc_preview")],
        [InlineKeyboardButton("🚀 Abhi Send Karo",         callback_data="bc_confirm")],
        [InlineKeyboardButton("❌ Cancel",                  callback_data="bc_cancel")],
    ])


def kb_bc_after_btn() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Aur Button Add Karo", callback_data="bc_add_btn")],
        [InlineKeyboardButton("👁️ Preview",            callback_data="bc_preview")],
        [InlineKeyboardButton("🚀 Send Karo",           callback_data="bc_confirm")],
        [InlineKeyboardButton("❌ Cancel",               callback_data="bc_cancel")],
    ])


def kb_bc_confirm() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Haan, Send Karo!", callback_data="bc_send")],
        [InlineKeyboardButton("✏️ Edit Karo",  callback_data="bc_preview"),
         InlineKeyboardButton("❌ Cancel",      callback_data="bc_cancel")],
    ])


# ════════════════════════════════════════════════
#              🏭 Bot factory
# ════════════════════════════════════════════════

def make_handlers(bk: str, label: str):
    """
    Returns all handlers for one bot instance.
    bk    = unique key e.g. "bot1"
    label = display name e.g. "🤖 Bot 1"
    """

    # ── panel text helper ────────────────────────
    def panel_text(s: dict) -> str:
        return (
            f"🛠️ <b>{label} — Admin Panel</b>\n\n"
            f"{'✅' if s['auto_approve'] else '❌'} Auto Approve: "
            f"<b>{'ON' if s['auto_approve'] else 'OFF'}</b>\n"
            f"📨 Message Type: <b>{s['message_type'].upper()}</b>\n"
            f"🔘 Inline Buttons: <b>{len(s['inline_buttons'])}</b>\n"
            f"👥 Registered Users: <b>{len(load_users(bk))}</b>\n\n"
            "Niche se choose karo 👇"
        )

    # ── /start ───────────────────────────────────
    async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not is_auth(uid):
            add_user(
                bk, uid,
                update.effective_user.first_name,
                update.effective_user.username or "",
            )
            await update.message.reply_text("👋 Only admins can use it ")
            return
        s = load_settings(bk)
        await update.message.reply_text(
            panel_text(s), reply_markup=kb_main(s), parse_mode=ParseMode.HTML
        )

    # ── /broadcast ───────────────────────────────
    async def bc_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not is_auth(update.effective_user.id):
            return
        ctx.user_data.clear()
        total = len(load_users(bk))
        await update.message.reply_text(
            f"📡 <b>{label} — Broadcast</b>\n\n"
            f"👥 Total registered users: <b>{total}</b>\n\n"
            "Kaunsa format mein bhejein? 👇",
            reply_markup=kb_bc_type(),
            parse_mode=ParseMode.HTML,
        )

    # ── Callback handler ─────────────────────────
    async def cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        q   = update.callback_query
        uid = q.from_user.id
        await q.answer()

        if not is_auth(uid):
            await q.answer("❌ Access denied!", show_alert=True)
            return

        d = q.data

        async def go_main():
            ns = load_settings(bk)
            await q.edit_message_text(
                panel_text(ns), reply_markup=kb_main(ns), parse_mode=ParseMode.HTML
            )

        # ── join message settings ──────────────────

        if d == "back_main":
            ctx.user_data.clear()
            await go_main()

        elif d == "toggle_approve":
            s = load_settings(bk)
            s["auto_approve"] = not s["auto_approve"]
            save_settings(bk, s)
            await q.answer(
                f"Auto Approve: {'✅ ON' if s['auto_approve'] else '❌ OFF'}",
                show_alert=True,
            )
            await go_main()

        elif d == "set_message":
            await q.edit_message_text(
                "📨 <b>Message Type Choose Karo</b>\n\n"
                "HTML supported:\n"
                "<code>&lt;b&gt;bold&lt;/b&gt;</code>  "
                "<code>&lt;i&gt;italic&lt;/i&gt;</code>  "
                "<code>&lt;a href='url'&gt;link&lt;/a&gt;</code>\n\n"
                "💡 <code>{name}</code> se user ka naam aayega",
                reply_markup=kb_msg_type(),
                parse_mode=ParseMode.HTML,
            )

        elif d.startswith("mt_"):
            mtype = d[3:]
            s = load_settings(bk)
            s["message_type"] = mtype
            save_settings(bk, s)
            ctx.user_data["aw"] = "text"
            hint = (
                "\n\n📸 <i>Text ke baad media bhi maangega.</i>"
                if mtype != "text"
                else ""
            )
            await q.edit_message_text(
                f"✏️ <b>Message text bhejo:</b>{hint}\n\n"
                "💡 <code>{name}</code> se user ka naam replace hoga",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Back", callback_data="set_message")]]
                ),
            )

        elif d == "manage_buttons":
            s = load_settings(bk)
            await q.edit_message_text(
                f"🔘 <b>Inline Buttons ({len(s['inline_buttons'])})</b>\n\nManage karo 👇",
                reply_markup=kb_btn_list(s),
                parse_mode=ParseMode.HTML,
            )

        elif d == "add_btn":
            ctx.user_data["aw"] = "btn_text"
            await q.edit_message_text(
                "🔘 <b>Button Add — Step 1/2</b>\n\nButton par kya text dikhna chahiye?",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("❌ Cancel", callback_data="manage_buttons")]]
                ),
            )

        elif d.startswith("rm_btn_"):
            idx = int(d[7:])
            s = load_settings(bk)
            removed = s["inline_buttons"].pop(idx)
            save_settings(bk, s)
            await q.answer(f"✅ '{removed['text']}' remove ho gaya!", show_alert=True)
            await q.edit_message_text(
                f"🔘 <b>Inline Buttons ({len(s['inline_buttons'])})</b>",
                reply_markup=kb_btn_list(s),
                parse_mode=ParseMode.HTML,
            )

        elif d == "preview":
            s = load_settings(bk)
            await q.edit_message_text("👁️ <b>Preview aa raha hai...</b>", parse_mode=ParseMode.HTML)
            try:
                await send_msg(
                    ctx.bot, q.message.chat_id,
                    s["message_type"], s["message_text"],
                    s["media_file_id"], s["inline_buttons"],
                )
            except Exception as e:
                await ctx.bot.send_message(q.message.chat_id, f"⚠️ Preview error:\n{e}")
            await ctx.bot.send_message(
                q.message.chat_id,
                "👆 Yeh preview hai!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚀 Publish", callback_data="publish")],
                    [InlineKeyboardButton("✏️ Edit",    callback_data="back_main")],
                ]),
            )

        elif d == "publish":
            s = load_settings(bk)
            save_settings(bk, s)
            await q.edit_message_text(
                f"✅ <b>{label} — Published!</b>\n\n"
                "Har join request pe yeh message jaayega. ✔️",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Main Menu", callback_data="back_main")]]
                ),
            )

        elif d == "stats":
            s  = load_settings(bk)
            st = s.get("stats", {"total": 0, "approved": 0})
            await q.edit_message_text(
                f"📊 <b>{label} — Stats</b>\n\n"
                f"📥 Total Requests: <b>{st['total']}</b>\n"
                f"✅ Approved: <b>{st['approved']}</b>\n"
                f"👥 Registered Users: <b>{len(load_users(bk))}</b>\n"
                f"🤖 Auto Approve: <b>{'ON' if s['auto_approve'] else 'OFF'}</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
                ),
            )

        # ── broadcast callbacks ────────────────────

        elif d == "bc_menu":
            ctx.user_data.clear()
            total = len(load_users(bk))
            await q.edit_message_text(
                f"📡 <b>{label} — Broadcast</b>\n\n"
                f"👥 Total users: <b>{total}</b>\n\n"
                "Kaunsa format? 👇",
                reply_markup=kb_bc_type(),
                parse_mode=ParseMode.HTML,
            )

        elif d.startswith("bc_t_"):
            bc_type = d[5:]
            ctx.user_data.update(
                {"bc_type": bc_type, "bc_buttons": [], "bc_text": "", "bc_media": None}
            )
            if bc_type == "text":
                ctx.user_data["aw"] = "bc_text"
                await q.edit_message_text(
                    "📝 <b>Broadcast text likho:</b>\n\n"
                    "HTML: <code>&lt;b&gt;bold&lt;/b&gt;</code>  "
                    "<code>&lt;i&gt;italic&lt;/i&gt;</code>\n"
                    "💡 <code>{name}</code> se user ka naam aayega",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("❌ Cancel", callback_data="bc_cancel")]]
                    ),
                )
            else:
                ctx.user_data["aw"] = "bc_media"
                word = "Photo" if bc_type == "photo" else "Video"
                await q.edit_message_text(
                    f"📤 <b>Apna {word} bhejo</b>\n\n"
                    "Caption bhi saath mein likh sakte ho (optional)\n"
                    "💡 Caption mein HTML aur <code>{name}</code> supported hai",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("❌ Cancel", callback_data="bc_cancel")]]
                    ),
                )

        elif d == "bc_add_btn":
            ctx.user_data["aw"] = "bc_btn_text"
            await q.edit_message_text(
                "🔘 <b>Broadcast Button — Step 1/2</b>\n\nButton par kya text dikhna chahiye?",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("❌ Cancel", callback_data="bc_cancel")]]
                ),
            )

        elif d == "bc_preview":
            bc_type  = ctx.user_data.get("bc_type", "text")
            bc_text  = ctx.user_data.get("bc_text", "")
            bc_media = ctx.user_data.get("bc_media")
            bc_btns  = ctx.user_data.get("bc_buttons", [])
            if not bc_text and not bc_media:
                await q.answer("⚠️ Pehle content set karo!", show_alert=True)
                return
            await q.edit_message_text("👁️ <b>Broadcast Preview...</b>", parse_mode=ParseMode.HTML)
            try:
                await send_msg(ctx.bot, q.message.chat_id, bc_type, bc_text, bc_media, bc_btns)
            except Exception as e:
                await ctx.bot.send_message(q.message.chat_id, f"⚠️ Preview error:\n{e}")
            total = len(load_users(bk))
            await ctx.bot.send_message(
                q.message.chat_id,
                f"👆 Yeh preview hai!\n\n👥 <b>{total} users</b> ko jaayega.",
                parse_mode=ParseMode.HTML,
                reply_markup=kb_bc_confirm(),
            )

        elif d == "bc_confirm":
            bc_text  = ctx.user_data.get("bc_text", "")
            bc_media = ctx.user_data.get("bc_media")
            if not bc_text and not bc_media:
                await q.answer("⚠️ Pehle content set karo!", show_alert=True)
                return
            total = len(load_users(bk))
            await q.edit_message_text(
                f"⚠️ <b>Confirm Karo!</b>\n\n"
                f"👥 <b>{total} users</b> ko message jaayega. Pakka?",
                parse_mode=ParseMode.HTML,
                reply_markup=kb_bc_confirm(),
            )

        elif d == "bc_send":
            bc_type  = ctx.user_data.get("bc_type", "text")
            bc_text  = ctx.user_data.get("bc_text", "")
            bc_media = ctx.user_data.get("bc_media")
            bc_btns  = ctx.user_data.get("bc_buttons", [])
            await q.edit_message_text(
                "📡 <b>Broadcast shuru ho gaya!</b>", parse_mode=ParseMode.HTML
            )
            ctx.user_data.clear()
            asyncio.create_task(
                do_broadcast(
                    ctx.bot, bk, label, q.message.chat_id,
                    bc_type, bc_text, bc_media, bc_btns,
                )
            )

        elif d == "bc_cancel":
            ctx.user_data.clear()
            await q.edit_message_text(
                "❌ <b>Broadcast cancel ho gaya.</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Main Menu", callback_data="back_main")]]
                ),
            )

    # ── Message handler ──────────────────────────
    async def msg_hdl(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id

        if not is_auth(uid):
            add_user(
                bk, uid,
                update.effective_user.first_name,
                update.effective_user.username or "",
            )
            return

        aw = ctx.user_data.get("aw")
        s  = load_settings(bk)

        # ── join message setup ──────────────────

        if aw == "text":
            text = update.message.text or update.message.caption or ""
            s["message_text"] = text
            save_settings(bk, s)
            ctx.user_data["aw"] = None
            if s["message_type"] in ("photo", "video"):
                ctx.user_data["aw"] = "media"
                word = "Photo" if s["message_type"] == "photo" else "Video"
                await update.message.reply_text(
                    f"✅ Text save!\n\nStep 2: Ab apna <b>{word}</b> bhejo 📤",
                    parse_mode=ParseMode.HTML,
                )
            else:
                await update.message.reply_text(
                    "✅ <b>Text save ho gaya!</b>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb_after_save(),
                )

        elif aw == "media":
            mt  = s["message_type"]
            fid = None
            if update.message.photo and mt == "photo":
                fid = update.message.photo[-1].file_id
            elif update.message.video and mt == "video":
                fid = update.message.video.file_id
            if fid:
                s["media_file_id"] = fid
                save_settings(bk, s)
                ctx.user_data["aw"] = None
                await update.message.reply_text(
                    "✅ <b>Media save ho gayi!</b>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb_after_save(),
                )
            else:
                await update.message.reply_text(
                    f"⚠️ <b>{'Photo' if mt == 'photo' else 'Video'}</b> chahiye!",
                    parse_mode=ParseMode.HTML,
                )

        elif aw == "btn_text":
            ctx.user_data["nb_text"] = update.message.text
            ctx.user_data["aw"]      = "btn_url"
            await update.message.reply_text(
                f"✅ Text: <b>{update.message.text}</b>\n\n"
                "Step 2/2: URL bhejo:\n<code>https://t.me/yourchannel</code>",
                parse_mode=ParseMode.HTML,
            )

        elif aw == "btn_url":
            url = update.message.text.strip()
            if not url.startswith("http"):
                await update.message.reply_text(
                    "⚠️ URL <code>https://</code> se shuru ho!",
                    parse_mode=ParseMode.HTML,
                )
                return
            bt = ctx.user_data.pop("nb_text", "Button")
            ctx.user_data["aw"] = None
            s["inline_buttons"].append({"text": bt, "url": url})
            save_settings(bk, s)
            await update.message.reply_text(
                f"✅ <b>Button add!</b>\n"
                f"Label: <b>{bt}</b>\nURL: <code>{url}</code>\n"
                f"Total: <b>{len(s['inline_buttons'])}</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=kb_after_btn(),
            )

        # ── broadcast setup ─────────────────────

        elif aw == "bc_text":
            ctx.user_data["bc_text"] = update.message.text or ""
            ctx.user_data["aw"]      = None
            await update.message.reply_text(
                "✅ <b>Broadcast text save!</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=kb_bc_after_content(),
            )

        elif aw == "bc_media":
            bc_type = ctx.user_data.get("bc_type", "photo")
            cap     = update.message.caption or ""
            fid     = None
            if update.message.photo and bc_type == "photo":
                fid = update.message.photo[-1].file_id
            elif update.message.video and bc_type == "video":
                fid = update.message.video.file_id
            if fid:
                ctx.user_data["bc_media"] = fid
                ctx.user_data["bc_text"]  = cap
                ctx.user_data["aw"]       = None
                preview = cap[:40] + "..." if len(cap) > 40 else cap or "(koi caption nahi)"
                await update.message.reply_text(
                    f"✅ <b>Media save!</b>\nCaption: {preview}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb_bc_after_content(),
                )
            else:
                word = "Photo" if bc_type == "photo" else "Video"
                await update.message.reply_text(
                    f"⚠️ <b>{word}</b> chahiye!", parse_mode=ParseMode.HTML
                )

        elif aw == "bc_btn_text":
            ctx.user_data["bc_nb_text"] = update.message.text
            ctx.user_data["aw"]         = "bc_btn_url"
            await update.message.reply_text(
                f"✅ Text: <b>{update.message.text}</b>\n\nStep 2/2: URL bhejo:",
                parse_mode=ParseMode.HTML,
            )

        elif aw == "bc_btn_url":
            url = update.message.text.strip()
            if not url.startswith("http"):
                await update.message.reply_text(
                    "⚠️ URL <code>https://</code> se shuru ho!",
                    parse_mode=ParseMode.HTML,
                )
                return
            bt = ctx.user_data.pop("bc_nb_text", "Button")
            ctx.user_data["aw"] = None
            ctx.user_data.setdefault("bc_buttons", []).append({"text": bt, "url": url})
            await update.message.reply_text(
                f"✅ <b>Button add!</b>\n"
                f"Label: <b>{bt}</b>\nURL: <code>{url}</code>\n"
                f"Total BC buttons: <b>{len(ctx.user_data['bc_buttons'])}</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=kb_bc_after_btn(),
            )

    # ── Join request handler ─────────────────────
    async def jr_hdl(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        jr   = update.chat_join_request
        uid  = jr.from_user.id
        name = jr.from_user.first_name
        s    = load_settings(bk)

        add_user(bk, uid, name, jr.from_user.username or "")

        st = s.get("stats", {"total": 0, "approved": 0})
        st["total"] += 1

        try:
            await send_msg(
                ctx.bot, uid,
                s["message_type"], s["message_text"],
                s["media_file_id"], s["inline_buttons"],
                name=name,
            )
            logger.info(f"[{label}] ✅ DM → {name} ({uid})")
        except Exception as e:
            logger.error(f"[{label}] ❌ DM fail → {uid}: {e}")

        if s.get("auto_approve", True):
            try:
                await jr.approve()
                st["approved"] += 1
                logger.info(f"[{label}] ✅ Approved → {name}")
            except Exception as e:
                logger.error(f"[{label}] ❌ Approve fail: {e}")

        s["stats"] = st
        save_settings(bk, s)

    return start_cmd, bc_cmd, cb, msg_hdl, jr_hdl


# ════════════════════════════════════════════════
#              🔧 Build application
# ════════════════════════════════════════════════

def build_app(token: str, bk: str, label: str) -> Application:
    sc, bcc, cb, mh, jr = make_handlers(bk, label)
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start",     sc))
    app.add_handler(CommandHandler("broadcast", bcc))
    app.add_handler(ChatJoinRequestHandler(jr))
    app.add_handler(CallbackQueryHandler(cb))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.VIDEO, mh))
    return app


# ════════════════════════════════════════════════
#              🚀 Run one bot in thread
# ════════════════════════════════════════════════

def run_bot(token: str, bk: str, label: str):
    async def runner():
        app = build_app(token, bk, label)
        logger.info(f"[{label}] Starting...")
        async with app:
            await app.initialize()
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)
            print(f"  ✅ {label} ready!")
            await asyncio.Event().wait()   # run forever

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(runner())


# ════════════════════════════════════════════════
#              🎬 Entry point
# ════════════════════════════════════════════════

def main():
    bots = cfg.ACTIVE_BOTS
    if not bots:
        print("❌ config.py mein koi valid token nahi mila!")
        return

    print("=" * 55)
    print("  JOIN REQUEST BOT — Starting")
    print(f"  Owner  : {cfg.OWNER_ID}")
    print(f"  Admins : {cfg.ADMIN_IDS}")
    print(f"  Active bots: {len(bots)}")
    for b in bots:
        print(f"    • {b['label']}  (key={b['key']})")
    print("=" * 55)

    threads = []
    for b in bots:
        t = threading.Thread(
            target=run_bot,
            args=(b["token"], b["key"], b["label"]),
            daemon=True,
            name=b["label"],
        )
        t.start()
        threads.append(t)

    print(f"\n✅ {len(threads)} bot(s) chal rahe hain! Ctrl+C se band karo.\n")

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all bots...")


if __name__ == "__main__":
    main()
