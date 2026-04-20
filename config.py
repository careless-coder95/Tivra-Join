# ╔══════════════════════════════════════════════════════════════╗
# ║                     config.py                               ║
# ║   Yahan sirf apni settings daalo — bot.py mat chhuo        ║
# ╚══════════════════════════════════════════════════════════════╝

# ── Owner & Admins ────────────────────────────────────────────
# Apna Telegram numeric ID yahan daalo
OWNER_ID = 5864182070

# Extra admins (OWNER_ID bhi is list mein hona chahiye)
ADMIN_IDS = [5864182070, 8260757052]


# ── Bot Tokens (1 se 10 tak) ──────────────────────────────────
# Jitne bots use karne hain utne tokens daalo.
# Baaki ko "" (empty) chhod do — woh bots automatically skip honge.
#
# Format: ("Token", "Label")
# Label woh naam hai jo admin panel mein dikhega.

BOT_LIST = [
    ("",  "🤖 Bot 1"),   # Bot 1
    ("",  "🤖 Bot 2"),   # Bot 2
    ("",               "🤖 Bot 3"),   # <- Khali = skip hoga
    ("",               "🤖 Bot 4"),
    ("",               "🤖 Bot 5"),
    ("",               "🤖 Bot 6"),
    ("",               "🤖 Bot 7"),
    ("",               "🤖 Bot 8"),
    ("",               "🤖 Bot 9"),
    ("",               "🤖 Bot 10"),
]


# ── /start Message (sabko dikhega — user + admin dono ko) ────
# START_IMG: Image ka file_id ya direct URL dono chalega.
#            Agar image nahi chahiye toh khali string "" chhod do.
START_IMG = "https://n.uguu.se/KjiANlrC.jpg"

# START_TEXT: HTML parse mode mein likho.
START_TEXT = f"""<blockquote expandable>𝗛𝗘𝗟𝗟𝗢 𝗨𝗦𝗘𝗥 ;</blockquote>
- 𝗦𝗜𝗠𝗣𝗟𝗘 & 𝗘𝗔𝗦𝗬 𝗧𝗔𝗦𝗞 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘 𝗞𝗔𝗥𝗞𝗘. 🛂

- 𝗔𝗣𝗣 ₹𝟰𝟬𝟬 𝗧𝗞 𝗘𝗔𝗥𝗡 𝗞𝗔𝗥 𝗦𝗔𝗞𝗧𝗘 𝗛𝗔𝗜. 🤑

- 𝗜𝗡𝗦𝗧𝗔𝗡𝗧 𝗨𝗣𝗜 𝗪𝗜𝗧𝗛𝗗𝗥𝗔𝗪𝗔𝗟 𝗔𝗩𝗜𝗟𝗔𝗕𝗟𝗘. 📤

- 𝗦𝗢, 𝗖𝗛𝗘𝗔𝗞 𝗙𝗔𝗦𝗧 𝗡𝗢𝗪 ⏱️

- 𝗗𝗘𝗟𝗔𝗬 𝗡𝗔 𝗞𝗔𝗥𝗘𝗡 ⏳
"""

# START_BUTTONS: /start message ke saath inline buttons.
# Agar button nahi chahiye toh [] khali list chhod do.
START_BUTTONS = [
    {"text": "✅ 𝗖𝗟𝗔𝗜𝗠 ₹𝟰𝟬𝟬 ✅", "url": "https://t.me/DailyxCash_bot"},
]


# ── Default Join Message ──────────────────────────────────────
# Yeh message tab jaata hai jab koi join request bhejta hai.
# Baad mein /start se panel se bhi change kar sakte ho.
DEFAULT_WELCOME_TEXT = (
    "👋 <b>Welcome!</b>\n\n"
    "Aapki join request receive ho gayi!\n"
    "💡 <code>{name}</code> — user ka naam automatically replace hota hai"
)

# ── Auto Approve Default ──────────────────────────────────────
# True  = join request automatically approve ho jaayegi
# False = manually approve karna padega
DEFAULT_AUTO_APPROVE = True


# ══════════════════════════════════════════════════════════════
# Niche kuch mat badlo — yeh internally use hota hai
# ══════════════════════════════════════════════════════════════

# Active bots: sirf woh jo non-empty token wale hain
ACTIVE_BOTS = [
    {"key": f"bot{i+1}", "token": token, "label": label}
    for i, (token, label) in enumerate(BOT_LIST)
    if token.strip()
]

# Settings + Users files automatically generate honge
SETTINGS_FILES = {b["key"]: f"settings_{b['key']}.json" for b in ACTIVE_BOTS}
USERS_FILES    = {b["key"]: f"users_{b['key']}.json"    for b in ACTIVE_BOTS}

DEFAULT_SETTINGS = {
    "auto_approve": DEFAULT_AUTO_APPROVE,
    "message_type": "text",
    "message_text": DEFAULT_WELCOME_TEXT,
    "media_file_id": None,
    "inline_buttons": [],
    "stats": {"total": 0, "approved": 0},
}
