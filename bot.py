import os
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Ambil token dari environment (supaya aman di GitHub Actions)
TOKEN = os.getenv("BOT_TOKEN")

# Fungsi ucapan selamat datang
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        full_name = member.full_name
        username = f"@{member.username}" if member.username else "-"
        user_id = member.id
        mention = f"<a href='tg://user?id={user_id}'>{full_name}</a>"
        date_now = datetime.now().strftime("%d/%m/%Y")
        group_name = update.message.chat.title

        text = (
f"क═══════क⊹⊱✫⊰⊹क═══════क\n"
f"  𖤍 𝐅𝐮𝐥𝐥 𝐍𝐚𝐦𝐞   : {full_name}\n"
f"  𖤍 𝐔𝐬𝐞𝐫 𝐍𝐚𝐦𝐞  : {username}\n"
f"  𖤍 𝐔𝐬𝐞𝐫 𝐈𝐃        : {user_id}\n"
f"  𖤍 𝐌𝐞𝐧𝐭𝐢𝐨𝐧       : {mention}\n"
f"  𖤍 𝐃𝐚𝐭𝐞             : {date_now}\n"
f"  𖤍 𝐆𝐫𝐨𝐮𝐩         : {group_name}\n\n"
f"𝐒𝐞𝐥𝐚𝐦𝐚𝐭 𝐝𝐚𝐭𝐚𝐧𝐠 , 𝐬𝐢𝐥𝐚𝐡𝐤𝐚𝐧 𝐦𝐞𝐦𝐛𝐚𝐜𝐚 𝐫𝐮𝐥𝐞𝐬 𝐠𝐫𝐨𝐮𝐩 !\n"
f"क═══════क⊹⊱✫⊰⊹क═══════क"
        )

        # Tombol aturan & perkenalan
        keyboard = [
            [InlineKeyboardButton("📜 Baca Aturan", url="https://t.me/namagrupkamu/123")],
            [InlineKeyboardButton("🙋 Perkenalan", callback_data="intro")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_html(text, reply_markup=reply_markup)

# Fungsi ucapan selamat tinggal
async def goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.message.left_chat_member
    if member:
        full_name = member.full_name
        username = f"@{member.username}" if member.username else "-"
        user_id = member.id
        mention = f"<a href='tg://user?id={user_id}'>{full_name}</a>"
        date_now = datetime.now().strftime("%d/%m/%Y")
        group_name = update.message.chat.title

        text = (
f"क═══════क⊹⊱✫⊰⊹क═══════क\n"
f"  𖤍 𝐅𝐮𝐥𝐥 𝐍𝐚𝐦𝐞   : {full_name}\n"
f"  𖤍 𝐔𝐬𝐞𝐫 𝐍𝐚𝐦𝐞  : {username}\n"
f"  𖤍 𝐔𝐬𝐞𝐫 𝐈𝐃        : {user_id}\n"
f"  𖤍 𝐌𝐞𝐧𝐭𝐢𝐨𝐧       : {mention}\n"
f"  𖤍 𝐃𝐚𝐭𝐞             : {date_now}\n"
f"  𖤍 𝐆𝐫𝐨𝐮𝐩         : {group_name}\n\n"
f"👋 𝐒𝐞𝐥𝐚𝐦𝐚𝐭 𝐭𝐢𝐧𝐠𝐠𝐚𝐥 , 𝐬𝐚𝐦𝐩𝐚𝐢 𝐣𝐮𝐦𝐩𝐚 𝐥𝐚𝐠𝐢 !\n"
f"क═══════क⊹⊱✫⊰⊹क═══════क"
        )

        await update.message.reply_html(text)

# Handler tombol
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "intro":
        await query.edit_message_text(
            text="Silakan perkenalkan diri kamu di grup ✨\n"
                 "Contoh: Nama, hobi, dan alasan join grup."
        )

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, goodbye))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Bot Welcome + Goodbye Estetik aktif...")
    app.run_polling()

if __name__ == "__main__":
    main()
