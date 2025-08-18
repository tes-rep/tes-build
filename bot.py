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

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Token bot (dari environment variable)
import os
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


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
# Kick User
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


# =========================
# Ban User
# =========================
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


# =========================
# Unban User
# =========================
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


# =========================
# Mute & Unmute
# =========================
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
# Help Command
# =========================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
🤖 Daftar Perintah Bot:

👋 Welcome & Goodbye
  - Otomatis saat user join / keluar

🗑️ Hapus Pesan
  - /delete → hapus pesan yang di-reply

👮 Admin Tools
  - /kick → keluarkan user sementara (reply pesan atau /kick <user_id>)
  - /ban → banned permanen (reply pesan atau /ban <user_id>)
  - /unban → buka banned (/unban <user_id>)
  - /mute → bisukan user (reply pesan atau /mute <user_id>)
  - /unmute → buka bisu user (reply pesan atau /unmute <user_id>)

ℹ️ Gunakan reply pesan atau user_id sesuai kebutuhan
"""
    await update.message.reply_text(text)


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

    print("🤖 Bot berjalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
