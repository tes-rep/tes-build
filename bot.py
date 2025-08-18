import logging
from datetime import datetime
from telegram import (
    Update, ChatPermissions,
    ChatMember
)
from telegram.ext import (
    Application, CommandHandler,
    ContextTypes, MessageHandler, filters
)
import os

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# =========================
# Storage rules grup
# =========================
GROUP_RULES = {}

# =========================
# Welcome otomatis
# =========================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        full_name = member.full_name
        username = f"@{member.username}" if member.username else "Tidak ada"
        user_id = member.id
        mention = member.mention_html()
        date = datetime.now().strftime("%d/%m/%Y")
        group_name = update.effective_chat.title

        text = f"""
क═══════क⊹⊱✫⊰⊹क═══════क
𖤍 𝐅𝐮𝐥𝐥 𝐍𝐚𝐦𝐞   : {full_name}
𖤍 𝐔𝐬𝐞𝐫 𝐍𝐚𝐦𝐞  : {username}
𖤍 𝐔𝐬𝐞𝐫 𝐈𝐃        : {user_id}
𖤍 𝐌𝐞𝐧𝐭𝐢𝐨𝐧       : {mention}
𖤍 𝐃𝐚𝐭𝐞             : {date}
𖤍 𝐆𝐫𝐨𝐮𝐩         : {group_name}

𝐒𝐞𝐥𝐚𝐦𝐚𝐭 𝐝𝐚𝐭𝐚𝐧𝐠 , 𝐬𝐢𝐥𝐚𝐡𝐤𝐚𝐧 𝐦𝐞𝐦𝐛𝐚𝐜𝐚 𝐫𝐮𝐥𝐞𝐬 𝐠𝐫𝐨𝐮𝐩 !
क═══════क⊹⊱✫⊰⊹क═══════क
"""
        await update.message.reply_html(text)

# =========================
# Goodbye otomatis
# =========================
async def goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.message.left_chat_member
    text = f"""
क═══════क⊹⊱✫⊰⊹क═══════क
👋 𝐒𝐞𝐥𝐚𝐦𝐚𝐭 𝐭𝐢𝐧𝐠𝐠𝐚𝐥, {member.full_name}
🆔 ID: {member.id}

Semoga sukses di perjalanan berikutnya 🌟
क═══════क⊹⊱✫⊰⊹क═══════क
"""
    await update.message.reply_html(text)

# =========================
# Hapus Pesan
# =========================
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        try:
            await update.message.reply_to_message.delete()
            await update.message.delete()
        except Exception as e:
            await update.message.reply_text(f"⚠️ Gagal hapus pesan: {e}")
    else:
        await update.message.reply_text("⚠️ Reply pesan yang ingin dihapus dengan /delete")

# =========================
# Kick / Ban / Unban / Mute / Unmute
# =========================
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        await update.message.reply_text("⚠️ Hanya admin yang bisa kick anggota.")
        return
    target_id = None
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif context.args:
        try:
            target_id = int(context.args[0])
        except:
            await update.message.reply_text("⚠️ Format salah. Gunakan /kick <user_id>")
            return
    if not target_id:
        await update.message.reply_text("⚠️ Harap reply pesan atau gunakan /kick <user_id>")
        return
    try:
        await context.bot.ban_chat_member(chat_id, target_id)
        await context.bot.unban_chat_member(chat_id, target_id)
        await update.message.reply_text(f"✅ User {target_id} telah dikeluarkan dari grup.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Gagal kick user: {e}")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        await update.message.reply_text("⚠️ Hanya admin yang bisa ban anggota.")
        return
    target_id = None
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif context.args:
        try:
            target_id = int(context.args[0])
        except:
            await update.message.reply_text("⚠️ Format salah. Gunakan /ban <user_id>")
            return
    if not target_id:
        await update.message.reply_text("⚠️ Harap reply pesan atau gunakan /ban <user_id>")
        return
    try:
        await context.bot.ban_chat_member(chat_id, target_id)
        await update.message.reply_text(f"⛔ User {target_id} telah di-banned permanen.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Gagal ban user: {e}")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        await update.message.reply_text("⚠️ Hanya admin yang bisa unban anggota.")
        return
    if not context.args:
        await update.message.reply_text("⚠️ Gunakan /unban <user_id>")
        return
    try:
        target_id = int(context.args[0])
        await context.bot.unban_chat_member(chat_id, target_id)
        await update.message.reply_text(f"✅ User {target_id} telah di-unban.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Gagal unban user: {e}")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        await update.message.reply_text("⚠️ Hanya admin yang bisa mute anggota.")
        return
    target_id = None
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif context.args:
        try:
            target_id = int(context.args[0])
        except:
            await update.message.reply_text("⚠️ Format salah. Gunakan /mute <user_id>")
            return
    if not target_id:
        await update.message.reply_text("⚠️ Harap reply pesan atau gunakan /mute <user_id>")
        return
    try:
        await context.bot.restrict_chat_member(
            chat_id, target_id, permissions=ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(f"🔇 User {target_id} telah di-mute.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Gagal mute user: {e}")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        await update.message.reply_text("⚠️ Hanya admin yang bisa unmute anggota.")
        return
    target_id = None
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif context.args:
        try:
            target_id = int(context.args[0])
        except:
            await update.message.reply_text("⚠️ Format salah. Gunakan /unmute <user_id>")
            return
    if not target_id:
        await update.message.reply_text("⚠️ Harap reply pesan atau gunakan /unmute <user_id>")
        return
    try:
        await context.bot.restrict_chat_member(
            chat_id, target_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=True
            )
        )
        await update.message.reply_text(f"🔊 User {target_id} telah di-unmute.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Gagal unmute user: {e}")

# =========================
# Help
# =========================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
🤖 Daftar Perintah Bot:

👋 Welcome & Goodbye
  - Otomatis saat user join / keluar

🗑️ Hapus Pesan
  - /delete → hapus pesan yang di-reply

👮 Admin Tools
  - /kick → keluarkan user sementara
  - /ban → banned permanen
  - /unban → buka banned
  - /mute → bisukan user
  - /unmute → buka bisu user
  - /pin → pin pesan (admin)
  - /unpin → lepas pin (admin)
  - /setrules → set rules grup (admin)
  - /rules → tampilkan rules grup

ℹ️ User Info
  - /whois <user_id> → info user
  - /info → info grup
  - /time → jam sekarang
  - /date → tanggal hari ini
"""
    await update.message.reply_text(text)

# =========================
# Info Grup & User
# =========================
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    members_count = await context.bot.get_chat_members_count(chat.id)
    admins = await context.bot.get_chat_administrators(chat.id)
    text = f"""
📌 Info Grup:
Nama: {chat.title}
ID: {chat.id}
Jumlah member: {members_count}
Jumlah admin: {len(admins)}
"""
    await update.message.reply_text(text)

async def whois(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan /whois <user_id>")
        return
    try:
        user_id = int(context.args[0])
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        user = member.user
        username = f"@{user.username}" if user.username else "Tidak ada"
        text = f"""
👤 Info User:
Full Name: {user.full_name}
Username: {username}
ID: {user.id}
"""
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Gagal ambil info user: {e}")

# =========================
# Time & Date
# =========================
async def time_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now().strftime("%H:%M:%S")
    await update.message.reply_text(f"🕒 Jam sekarang: {now}")

async def date_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime("%d/%m/%Y")
    await update.message.reply_text(f"📅 Tanggal hari ini: {today}")

# =========================
# Rules
# =========================
async def set_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        await update.message.reply_text("⚠️ Hanya admin yang bisa set rules.")
        return
    if not context.args:
        await update.message.reply_text("Gunakan /setrules <teks rules>")
        return
    GROUP_RULES[chat_id] = " ".join(context.args)
    await update.message.reply_text("✅ Rules grup berhasil disimpan.")

async def get_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    rules = GROUP_RULES.get(chat_id, "Rules belum diset.")
    await update.message.reply_text(f"📜 Rules Grup:\n{rules}")

# =========================
# Pin / Unpin
# =========================
async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        await update.message.reply_text("⚠️ Hanya admin yang bisa pin pesan.")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply pesan yang ingin di-pin.")
        return
    try:
        await update.message.reply_to_message.pin()
        await update.message.reply_text("📌 Pesan berhasil di-pin.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Gagal pin pesan: {e}")

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        await update.message.reply_text("⚠️ Hanya admin yang bisa unpin pesan.")
        return
    try:
        await context.bot.unpin_all_chat_messages(chat_id)
        await update.message.reply_text("📌 Semua pesan berhasil di-unpin.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Gagal unpin pesan: {e}")

# =========================
# Main App
# =========================
def main():
    app = Application.builder().token(TOKEN).build()

    # Event handler
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, goodbye))

    # Command handler
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("whois", whois))
    app.add_handler(CommandHandler("time", time_cmd))
    app.add_handler(CommandHandler("date", date_cmd))
    app.add_handler(CommandHandler("setrules", set_rules))
    app.add_handler(CommandHandler("rules", get_rules))
    app.add_handler(CommandHandler("pin", pin))
    app.add_handler(CommandHandler("unpin", unpin))

    print("🤖 Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
