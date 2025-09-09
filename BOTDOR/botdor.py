import os
import json
import uuid
import requests
import time
import logging
import base64
import qrcode
import io
import html
import re
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from crypto_helper import (
    API_KEY, encryptsign_xdata, java_like_timestamp, ts_gmt7_without_colon, 
    ax_api_signature, decrypt_xdata, get_x_signature_payment, get_x_signature_bounty,
    build_encrypted_field, display_html
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global variables
USER_STATES = {}
USER_TOKENS = {}
USER_API_KEYS = {}

BASE_URL = "https://api.myxl.xlaxiata.co.id"

class MyXLBot:
    def __init__(self, token):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.setup_handlers()

    def setup_handlers(self):
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("login", self.login))
        self.application.add_handler(CommandHandler("balance", self.balance))
        self.application.add_handler(CommandHandler("packages", self.packages))
        self.application.add_handler(CommandHandler("my_packages", self.my_packages))
        self.application.add_handler(CommandHandler("buy", self.buy))
        self.application.add_handler(CommandHandler("profile", self.profile))
        self.application.add_handler(CommandHandler("logout", self.logout))
        self.application.add_handler(CommandHandler("family", self.family))
        self.application.add_handler(CommandHandler("accounts", self.accounts))
        self.application.add_handler(CommandHandler("apikey", self.apikey))
        self.application.add_handler(CommandHandler("menu", self.main_menu))

        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_main_menu(update, context)

    async def main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_main_menu(update, context)

    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("🔑 Login", callback_data="menu_login")],
            [InlineKeyboardButton("💰 Cek Saldo", callback_data="menu_balance")],
            [InlineKeyboardButton("📦 Paket", callback_data="menu_packages")],
            [InlineKeyboardButton("🛒 Beli Paket", callback_data="menu_buy")],
            [InlineKeyboardButton("👤 Profil", callback_data="menu_profile")],
            [InlineKeyboardButton("⚙️ Pengaturan", callback_data="menu_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'message'):
            await update.message.reply_text("🏠 Menu Utama MyXL Bot:", reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text("🏠 Menu Utama MyXL Bot:", reply_markup=reply_markup)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        data = query.data

        try:
            if data == "menu_login":
                await self.handle_login_menu(update, context)
            elif data == "menu_balance":
                await self.handle_balance(update, context)
            elif data == "menu_packages":
                await self.handle_packages_menu(update, context)
            elif data == "menu_my_packages":
                await self.handle_my_packages(update, context)
            elif data == "menu_buy":
                await self.handle_buy_menu(update, context)
            elif data == "menu_profile":
                await self.handle_profile(update, context)
            elif data == "menu_settings":
                await self.handle_settings_menu(update, context)

            # Login submenu
            elif data == "login_main":
                await self.handle_login_menu(update, context)
            elif data == "login_new":
                await self.start_login_flow(update, context)
            elif data == "login_saved":
                await self.show_saved_accounts(update, context)
            elif data.startswith("account_"):
                await self.handle_account_selection(update, context, data)

            # Packages submenu
            elif data == "packages_xut":
                await self.handle_package_xut(update, context)
            elif data == "packages_family":
                await self.start_family_code_flow(update, context)
            elif data == "packages_my":
                await self.handle_my_packages(update, context)
            elif data == "packages_back":
                await self.handle_packages_menu(update, context)

            # Settings submenu
            elif data == "settings_apikey":
                await self.start_api_key_flow(update, context)
            elif data == "settings_accounts":
                await self.show_account_management(update, context)
            elif data == "settings_back":
                await self.handle_settings_menu(update, context)

            # Payment methods
            elif data.startswith("payment_"):
                await self.handle_payment_selection(update, context, data)

            # Confirmation
            elif data == "confirm_yes":
                await self.handle_purchase_confirmation(update, context, True)
            elif data == "confirm_no":
                await self.handle_purchase_confirmation(update, context, False)

            # Navigation
            elif data == "back_main":
                await self.show_main_menu(update, context)
            elif data == "back_prev":
                await self.handle_go_back(update, context)

            else:
                await query.edit_message_text("❌ Perintah tidak dikenali")

        except Exception as e:
            logger.error(f"Callback error: {e}")
            await query.edit_message_text("❌ Terjadi error. Silakan coba lagi.")

    # ========= MENU HANDLERS ========= #
    async def handle_login_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("🔑 Login Baru", callback_data="login_new")],
            [InlineKeyboardButton("📱 Akun Tersimpan", callback_data="login_saved")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_main")]
        ]
        await update.callback_query.edit_message_text(
            "🔐 Menu Login\n\nPilih opsi:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_data = USER_TOKENS.get(user_id)
        
        if not user_data or 'tokens' not in user_data:
            keyboard = [[InlineKeyboardButton("🔑 Login", callback_data="menu_login")]]
            await update.callback_query.edit_message_text(
                "❌ Silakan login terlebih dahulu",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        try:
            api_key = USER_API_KEYS.get(user_id)
            balance = get_balance(api_key, user_data['tokens']['id_token'])
            await update.callback_query.edit_message_text(
                f"💳 Informasi Saldo:\n"
                f"Nomor: {user_data['phone_number']}\n"
                f"Pulsa: Rp {balance['remaining']}\n"
                f"Masa aktif: {datetime.fromtimestamp(balance['expired_at']).strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception as e:
            logger.error(f"Balance error: {e}")
            await update.callback_query.edit_message_text("❌ Gagal mengambil informasi saldo")

    async def handle_packages_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📦 Paket XUT", callback_data="packages_xut")],
            [InlineKeyboardButton("🔍 Paket by Family Code", callback_data="packages_family")],
            [InlineKeyboardButton("📊 Paket Saya", callback_data="packages_my")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_main")]
        ]
        await update.callback_query.edit_message_text(
            "📦 Menu Paket\n\nPilih jenis paket:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_my_packages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_data = USER_TOKENS.get(user_id)
        
        if not user_data or 'tokens' not in user_data:
            keyboard = [[InlineKeyboardButton("🔑 Login", callback_data="menu_login")]]
            await update.callback_query.edit_message_text(
                "❌ Silakan login terlebih dahulu",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        try:
            api_key = USER_API_KEYS.get(user_id)
            my_packages = fetch_my_packages(api_key, user_data['tokens'])
            if not my_packages:
                await update.callback_query.edit_message_text("📭 Tidak ada paket aktif")
                return

            message = "📦 Paket Aktif Anda:\n\n"
            for i, pkg in enumerate(my_packages, 1):
                message += f"{i}. {pkg['name']}\n"
                message += f"   Kode: {pkg['quota_code']}\n"
                message += f"   Group: {pkg['group_code']}\n"
                message += f"   Family: {pkg['family_code']}\n\n"

            await update.callback_query.edit_message_text(message)
        except Exception as e:
            logger.error(f"My packages error: {e}")
            await update.callback_query.edit_message_text("❌ Gagal mengambil paket aktif")

    async def handle_buy_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_data = USER_TOKENS.get(user_id)
        
        if not user_data or 'tokens' not in user_data:
            keyboard = [[InlineKeyboardButton("🔑 Login", callback_data="menu_login")]]
            await update.callback_query.edit_message_text(
                "❌ Silakan login terlebih dahulu",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        keyboard = [
            [InlineKeyboardButton("💵 Pulsa", callback_data="payment_pulsa")],
            [InlineKeyboardButton("📱 E-Wallet", callback_data="payment_ewallet")],
            [InlineKeyboardButton("📲 QRIS", callback_data="payment_qris")],
            [InlineKeyboardButton("🎁 Bounty", callback_data="payment_bounty")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_main")]
        ]
        await update.callback_query.edit_message_text(
            "💳 Pilih metode pembayaran:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_data = USER_TOKENS.get(user_id)
        
        if not user_data or 'profile' not in user_data:
            keyboard = [[InlineKeyboardButton("🔑 Login", callback_data="menu_login")]]
            await update.callback_query.edit_message_text(
                "❌ Silakan login terlebih dahulu",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        profile = user_data['profile']['profile']
        await update.callback_query.edit_message_text(
            f"👤 Profil Akun:\n"
            f"Nomor: {profile['msisdn']}\n"
            f"Nama: {profile.get('name', 'Tidak tersedia')}\n"
            f"Email: {profile.get('email', 'Tidak tersedia')}\n"
            f"Status: {profile['status']}"
        )

    async def handle_settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("🔑 API Key", callback_data="settings_apikey")],
            [InlineKeyboardButton("👥 Kelola Akun", callback_data="settings_accounts")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_main")]
        ]
        await update.callback_query.edit_message_text(
            "⚙️ Menu Pengaturan\n\nPilih opsi:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ========= LOGIN FLOW ========= #
    async def start_login_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        # Check API key first
        api_key = USER_API_KEYS.get(user_id)
        if not api_key:
            USER_STATES[user_id] = {'state': 'awaiting_api_key', 'next_action': 'login'}
            await update.callback_query.edit_message_text("🔑 Silakan set API Key terlebih dahulu dengan mengetik /apikey")
            return
        
        USER_STATES[user_id] = {'state': 'awaiting_number'}
        await update.callback_query.edit_message_text("📱 Masukkan nomor XL Anda (contoh: 6281234567890):")

    async def show_saved_accounts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        saved_accounts = self.get_user_accounts(user_id)
        
        if not saved_accounts:
            keyboard = [[InlineKeyboardButton("➕ Tambah Akun Baru", callback_data="login_new")]]
            await update.callback_query.edit_message_text(
                "❌ Tidak ada akun tersimpan",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        keyboard = []
        for i, account in enumerate(saved_accounts, 1):
            keyboard.append([InlineKeyboardButton(f"{i}. {account['phone_number']}", callback_data=f"account_{i}")])
        
        keyboard.append([InlineKeyboardButton("➕ Tambah Akun Baru", callback_data="login_new")])
        keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="login_main")])
        
        await update.callback_query.edit_message_text(
            "📱 Akun Tersimpan:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_account_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        user_id = update.effective_user.id
        account_index = int(data.replace("account_", "")) - 1
        saved_accounts = self.get_user_accounts(user_id)
        
        if account_index < 0 or account_index >= len(saved_accounts):
            await update.callback_query.edit_message_text("❌ Akun tidak valid")
            return
        
        account = saved_accounts[account_index]
        
        try:
            # Try to refresh token
            tokens = get_new_token(account['refresh_token'])
            profile = get_profile(USER_API_KEYS[user_id], tokens['access_token'], tokens['id_token'])
            
            USER_TOKENS[user_id] = {
                'phone_number': account['phone_number'],
                'tokens': tokens,
                'profile': profile
            }
            
            await update.callback_query.edit_message_text(
                f"✅ Login berhasil! Selamat datang {profile['profile']['msisdn']}"
            )
        except Exception as e:
            logger.error(f"Account selection error: {e}")
            await update.callback_query.edit_message_text(
                "❌ Gagal login dengan akun tersimpan. Silakan login manual."
            )

    # ========= PACKAGES ========= #
    async def handle_package_xut(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_data = USER_TOKENS.get(user_id)
        api_key = USER_API_KEYS.get(user_id)
        
        if not user_data or not api_key:
            keyboard = [[InlineKeyboardButton("🔑 Login", callback_data="menu_login")]]
            await update.callback_query.edit_message_text(
                "❌ Silakan login terlebih dahulu",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        try:
            packages = get_package_xut(api_key, user_data['tokens'])
            if not packages:
                await update.callback_query.edit_message_text("❌ Tidak ada paket XUT ditemukan")
                return

            message = "📦 Paket XUT Tersedia:\n\n"
            for i, pkg in enumerate(packages, 1):
                message += f"{i}. {pkg['name']} - Rp {pkg['price']}\n"

            USER_STATES[user_id] = {
                'state': 'awaiting_package_selection',
                'packages': packages,
                'type': 'xut'
            }

            keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="packages_back")]]
            await update.callback_query.edit_message_text(
                message + "\nPilih nomor paket yang diinginkan:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Package XUT error: {e}")
            await update.callback_query.edit_message_text("❌ Gagal mengambil paket XUT")

    async def start_family_code_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        USER_STATES[user_id] = {'state': 'awaiting_family_code'}
        await update.callback_query.edit_message_text("🔍 Masukkan Family Code (contoh: 08a3b1e6-8e78-4e45-a540-b40f06871cfe):")

    # ========= SETTINGS ========= #
    async def start_api_key_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        USER_STATES[user_id] = {'state': 'awaiting_api_key'}
        await update.callback_query.edit_message_text("🔑 Masukkan API Key Anda:")

    async def show_account_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        saved_accounts = self.get_user_accounts(user_id)
        
        if not saved_accounts:
            await update.callback_query.edit_message_text("❌ Tidak ada akun tersimpan")
            return

        keyboard = []
        for i, account in enumerate(saved_accounts, 1):
            is_active = USER_TOKENS.get(user_id, {}).get('phone_number') == account['phone_number']
            status = " ✅" if is_active else ""
            keyboard.append([InlineKeyboardButton(f"{i}. {account['phone_number']}{status}", callback_data=f"manage_account_{i}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="settings_back")])
        
        await update.callback_query.edit_message_text(
            "👥 Akun Tersimpan:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ========= PAYMENT HANDLERS ========= #
    async def handle_payment_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        query = update.callback_query
        await query.answer()
        
        payment_method = data.replace('payment_', '')
        user_id = query.from_user.id
        user_data = USER_TOKENS.get(user_id)
        api_key = USER_API_KEYS.get(user_id)
        
        if not user_data or not api_key:
            await query.edit_message_text("❌ Silakan login terlebih dahulu")
            return

        # Get selected package from state
        state = USER_STATES.get(user_id, {})
        if not state.get('selected_package'):
            await query.edit_message_text("❌ Tidak ada paket yang dipilih")
            return

        selected_package = state['selected_package']
        package_details = state.get('package_details', {})

        try:
            if payment_method == 'pulsa':
                result = purchase_package(api_key, user_data['tokens'], selected_package['code'])
                if result and result.get('status') == 'SUCCESS':
                    await query.edit_message_text("✅ Pembelian berhasil! Paket akan segera aktif.")
                else:
                    error_msg = result.get('message', 'Unknown error') if result else 'Unknown error'
                    await query.edit_message_text(f"❌ Pembelian gagal: {error_msg}")
                    
            elif payment_method == 'qris':
                await self.handle_qris_payment(query, api_key, user_data['tokens'], selected_package, package_details)
                
            elif payment_method == 'bounty':
                await self.handle_bounty_payment(query, api_key, user_data['tokens'], selected_package, package_details)
                
            elif payment_method == 'ewallet':
                await query.edit_message_text("⚠️ Pembayaran E-Wallet sedang dalam pengembangan")
                
            else:
                await query.edit_message_text("❌ Metode pembayaran tidak dikenali")
                
        except Exception as e:
            logger.error(f"Payment error: {e}")
            await query.edit_message_text("❌ Gagal memproses pembayaran")

    async def handle_qris_payment(self, query, api_key: str, tokens: dict, selected_package: dict, package_details: dict):
        await query.edit_message_text("🔄 Membuat pembayaran QRIS...")
        
        try:
            token_confirmation = package_details.get("token_confirmation", "")
            if not token_confirmation:
                await query.edit_message_text("❌ Gagal mendapatkan token konfirmasi")
                return

            # Get payment methods
            payment_methods_data = get_payment_methods(
                api_key=api_key,
                tokens=tokens,
                token_confirmation=token_confirmation,
                payment_target=selected_package['code'],
            )
            
            if not payment_methods_data:
                await query.edit_message_text("❌ Gagal mendapatkan metode pembayaran")
                return

            token_payment = payment_methods_data["token_payment"]
            ts_to_sign = payment_methods_data["timestamp"]
            
            # Create QRIS transaction
            transaction_id = settlement_qris(
                api_key,
                tokens,
                token_payment,
                ts_to_sign,
                selected_package['code'],
                selected_package['price'],
                selected_package['name']
            )
            
            if not transaction_id:
                await query.edit_message_text("❌ Gagal membuat transaksi QRIS")
                return

            # Get QRIS code
            await query.edit_message_text("🔄 Mengambil kode QRIS...")
            qris_code = get_qris_code(api_key, tokens, transaction_id)
            
            if not qris_code:
                await query.edit_message_text("❌ Gagal mendapatkan kode QRIS")
                return

            # Generate QR code image
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qris_code)
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            img_buffer = io.BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Generate shareable link
            qris_b64 = base64.urlsafe_b64encode(qris_code.encode()).decode()
            qris_url = f"https://ki-ar-kod.netlify.app/?data={qris_b64}"
            
            # Send QR code to user
            caption = (f"💳 QRIS Payment\n\n"
                      f"📦 Paket: {selected_package['name']}\n"
                      f"💰 Harga: Rp {selected_package['price']:,}\n\n"
                      f"🔗 Link QRIS: {qris_url}\n\n"
                      f"⏰ QRIS akan kadaluarsa dalam 24 jam")
            
            await query.message.reply_photo(
                photo=img_buffer,
                caption=caption,
                parse_mode='HTML'
            )
            
            await query.edit_message_text("✅ QRIS berhasil dibuat! Silakan scan QR code di atas")
            
        except Exception as e:
            logger.error(f"QRIS payment error: {e}")
            await query.edit_message_text("❌ Gagal membuat pembayaran QRIS")

    async def handle_bounty_payment(self, query, api_key: str, tokens: dict, selected_package: dict, package_details: dict):
        await query.edit_message_text("🔄 Memproses pembayaran dengan Bounty...")
        
        try:
            token_confirmation = package_details.get("token_confirmation", "")
            if not token_confirmation:
                await query.edit_message_text("❌ Gagal mendapatkan token konfirmasi")
                return

            # Get payment methods
            payment_methods_data = get_payment_methods(
                api_key=api_key,
                tokens=tokens,
                token_confirmation=token_confirmation,
                payment_target=selected_package['code'],
            )
            
            if not payment_methods_data:
                await query.edit_message_text("❌ Gagal mendapatkan metode pembayaran")
                return

            token_payment = payment_methods_data["token_payment"]
            ts_to_sign = payment_methods_data["timestamp"]
            
            # Process bounty payment
            result = settlement_bounty(
                api_key,
                tokens,
                token_confirmation,
                ts_to_sign,
                selected_package['code'],
                selected_package['price'],
                selected_package['name']
            )
            
            if result and result.get('status') == 'SUCCESS':
                await query.edit_message_text("✅ Pembelian dengan Bounty berhasil! Paket akan segera aktif.")
            else:
                error_msg = result.get('message', 'Unknown error') if result else 'Unknown error'
                await query.edit_message_text(f"❌ Pembelian dengan Bounty gagal: {error_msg}")
                
        except Exception as e:
            logger.error(f"Bounty payment error: {e}")
            await query.edit_message_text("❌ Gagal memproses pembayaran Bounty")

    async def handle_purchase_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, confirm: bool):
        if confirm:
            user_id = update.effective_user.id
            state = USER_STATES.get(user_id)
            user_data = USER_TOKENS.get(user_id)
            api_key = USER_API_KEYS.get(user_id)
            
            if not state or 'selected_package' not in state or not user_data or not api_key:
                await update.callback_query.edit_message_text("❌ Session expired")
                return

            try:
                selected_package = state['selected_package']
                result = purchase_package(api_key, user_data['tokens'], selected_package['code'])

                if result and result.get('status') == 'SUCCESS':
                    await update.callback_query.edit_message_text("✅ Pembelian berhasil! Paket akan segera aktif.")
                else:
                    error_msg = result.get('message', 'Unknown error') if result else 'Unknown error'
                    await update.callback_query.edit_message_text(f"❌ Pembelian gagal: {error_msg}")
            except Exception as e:
                logger.error(f"Purchase error: {e}")
                await update.callback_query.edit_message_text("❌ Gagal memproses pembelian")
        else:
            await update.callback_query.edit_message_text("❌ Pembelian dibatalkan")

        if user_id in USER_STATES:
            del USER_STATES[user_id]

    # ========= NAVIGATION ========= #
    async def handle_go_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_main_menu(update, context)

    # ========= ORIGINAL COMMAND HANDLERS (for text commands) ========= #
    async def login(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.handle_login_menu(update, context)

    async def balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.handle_balance(update, context)

    async def packages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.handle_packages_menu(update, context)

    async def my_packages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.handle_my_packages(update, context)

    async def buy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.handle_buy_menu(update, context)

    async def profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.handle_profile(update, context)

    async def logout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id in USER_TOKENS:
            del USER_TOKENS[user_id]
        if user_id in USER_STATES:
            del USER_STATES[user_id]
        await update.message.reply_text("✅ Logout berhasil!")

    async def family(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        USER_STATES[user_id] = {'state': 'awaiting_family_code'}
        await update.message.reply_text("🔍 Masukkan Family Code (contoh: 08a3b1e6-8e78-4e45-a540-b40f06871cfe):")

    async def accounts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_account_management(update, context)

    async def apikey(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        USER_STATES[user_id] = {'state': 'awaiting_api_key'}
        await update.message.reply_text("🔑 Masukkan API Key Anda:")

    # ========= MESSAGE PROCESSING ========= #
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text
        state = USER_STATES.get(user_id, {}).get('state')

        if not state:
            await update.message.reply_text("ℹ️ Ketik /menu untuk melihat menu utama")
            return

        if state == 'awaiting_api_key':
            await self.process_api_key(update, text)
        elif state == 'awaiting_number':
            await self.process_phone_number(update, text)
        elif state == 'awaiting_otp':
            await self.process_otp(update, text)
        elif state == 'awaiting_family_code':
            await self.process_family_code(update, text)
        elif state == 'awaiting_package_selection':
            await self.process_package_selection(update, text)
        elif state == 'awaiting_payment_confirmation':
            await self.process_payment_confirmation(update, text)

    async def process_api_key(self, update: Update, api_key: str):
        user_id = update.effective_user.id
        try:
            if verify_api_key(api_key):
                USER_API_KEYS[user_id] = api_key
                self.save_user_api_key(user_id, api_key)
                next_action = USER_STATES[user_id].get('next_action')
                
                await update.message.reply_text("✅ API Key valid dan tersimpan!")
                
                if next_action == 'login':
                    del USER_STATES[user_id]
                    await self.start_login_flow(update, None)
                else:
                    del USER_STATES[user_id]
                    await self.show_main_menu(update, None)
            else:
                await update.message.reply_text("❌ API Key tidak valid. Silakan coba lagi:")
        except Exception as e:
            logger.error(f"API key error: {e}")
            await update.message.reply_text("❌ Gagal memverifikasi API Key. Silakan coba lagi:")

    async def process_phone_number(self, update: Update, phone_number: str):
        user_id = update.effective_user.id
        api_key = USER_API_KEYS.get(user_id)
        
        if not api_key:
            await update.message.reply_text("❌ API Key tidak ditemukan. Silakan set dengan /apikey")
            return

        if not validate_contact(phone_number):
            await update.message.reply_text("❌ Format nomor tidak valid. Contoh: 6281234567890")
            return

        try:
            subscriber_id = get_otp(phone_number)
            USER_STATES[user_id] = {
                'state': 'awaiting_otp',
                'phone_number': phone_number,
                'subscriber_id': subscriber_id
            }
            await update.message.reply_text("✅ OTP telah dikirim. Masukkan 6 digit kode OTP:")
        except Exception as e:
            logger.error(f"OTP error: {e}")
            await update.message.reply_text("❌ Gagal mengirim OTP. Silakan coba lagi.")

    async def process_otp(self, update: Update, otp: str):
        user_id = update.effective_user.id
        state = USER_STATES.get(user_id)
        api_key = USER_API_KEYS.get(user_id)
        
        if not state or 'phone_number' not in state or not api_key:
            await update.message.reply_text("❌ Session expired. Silakan mulai ulang dengan /login")
            return

        if not otp.isdigit() or len(otp) != 6:
            await update.message.reply_text("❌ OTP harus 6 digit angka")
            return

        try:
            tokens = submit_otp(api_key, state['phone_number'], otp)
            profile = get_profile(api_key, tokens['access_token'], tokens['id_token'])
            
            USER_TOKENS[user_id] = {
                'phone_number': state['phone_number'],
                'tokens': tokens,
                'profile': profile
            }

            # Save account
            self.save_user_account(user_id, {
                'phone_number': state['phone_number'],
                'refresh_token': tokens['refresh_token']
            })

            del USER_STATES[user_id]
            await update.message.reply_text(f"✅ Login berhasil! Selamat datang {profile['profile']['msisdn']}")
        except Exception as e:
            logger.error(f"Login error: {e}")
            await update.message.reply_text("❌ OTP tidak valid. Silakan coba lagi.")

    async def process_family_code(self, update: Update, family_code: str):
        user_id = update.effective_user.id
        user_data = USER_TOKENS.get(user_id)
        api_key = USER_API_KEYS.get(user_id)
        
        if not user_data or not api_key:
            await update.message.reply_text("❌ Silakan login terlebih dahulu")
            return

        try:
            packages = get_packages_by_family(api_key, user_data['tokens'], family_code)
            if not packages:
                await update.message.reply_text("❌ Tidak ada paket ditemukan untuk family code tersebut")
                return

            USER_STATES[user_id] = {
                'state': 'awaiting_package_selection',
                'packages': packages,
                'type': 'family'
            }

            message = f"📦 Paket untuk Family Code {family_code}:\n\n"
            for i, pkg in enumerate(packages, 1):
                message += f"{i}. {pkg['name']} - Rp {pkg['price']}\n"

            await update.message.reply_text(message + "\nPilih nomor paket yang diinginkan:")
        except Exception as e:
            logger.error(f"Family code error: {e}")
            await update.message.reply_text("❌ Family code tidak valid atau tidak ditemukan")

    async def process_package_selection(self, update: Update, selection: str):
        user_id = update.effective_user.id
        state = USER_STATES.get(user_id)
        user_data = USER_TOKENS.get(user_id)
        api_key = USER_API_KEYS.get(user_id)
        
        if not state or 'packages' not in state or not user_data or not api_key:
            await update.message.reply_text("❌ Session expired")
            return

        try:
            index = int(selection) - 1
            if index < 0 or index >= len(state['packages']):
                await update.message.reply_text("❌ Pilihan tidak valid")
                return

            selected_package = state['packages'][index]
            package_details = get_package(api_key, user_data['tokens'], selected_package['code'])
            
            # Build package info message
            message = f"📦 Detail Paket:\nNama: {selected_package['name']}\nHarga: Rp {selected_package['price']}\n\n"
            
            # Add benefits
            if package_details.get('package_option', {}).get('benefits'):
                message += "Benefits:\n"
                for benefit in package_details['package_option']['benefits']:
                    message += f"- {benefit['name']}: {benefit['total']}\n"
                message += "\n"
            
            # Add TNC
            if package_details.get('package_option', {}).get('tnc'):
                tnc_text = display_html(package_details['package_option']['tnc'])
                message += f"Syarat & Ketentuan:\n{tnc_text}\n"

            USER_STATES[user_id] = {
                'state': 'awaiting_payment_confirmation',
                'selected_package': selected_package,
                'package_details': package_details
            }

            keyboard = [
                [InlineKeyboardButton("✅ Ya", callback_data="confirm_yes"),
                 InlineKeyboardButton("❌ Tidak", callback_data="confirm_no")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(message)
            await update.message.reply_text("💳 Lanjutkan pembelian?", reply_markup=reply_markup)

        except (ValueError, IndexError):
            await update.message.reply_text("❌ Pilihan tidak valid")
        except Exception as e:
            logger.error(f"Package selection error: {e}")
            await update.message.reply_text("❌ Gagal mengambil detail paket")

    async def process_payment_confirmation(self, update: Update, confirmation: str):
        user_id = update.effective_user.id
        state = USER_STATES.get(user_id)

        if not state or 'selected_package' not in state:
            await update.message.reply_text("❌ Session expired")
            return

        if confirmation.lower() in ['ya', 'yes', 'y', 'ok']:
            user_data = USER_TOKENS.get(user_id)
            api_key = USER_API_KEYS.get(user_id)

            if not user_data or not api_key:
                await update.message.reply_text("❌ Silakan login terlebih dahulu")
                return

            try:
                selected_package = state['selected_package']
                result = purchase_package(api_key, user_data['tokens'], selected_package['code'])

                if result and result.get('status') == 'SUCCESS':
                    await update.message.reply_text("✅ Pembelian berhasil! Paket akan segera aktif.")
                else:
                    error_msg = result.get('message', 'Unknown error') if result else 'Unknown error'
                    await update.message.reply_text(f"❌ Pembelian gagal: {error_msg}")
            except Exception as e:
                logger.error(f"Purchase error: {e}")
                await update.message.reply_text("❌ Gagal memproses pembelian")
        else:
            await update.message.reply_text("❌ Pembelian dibatalkan")

        if user_id in USER_STATES:
            del USER_STATES[user_id]

    # Helper methods for user data persistence
    def get_user_accounts(self, user_id):
        try:
            if os.path.exists(f'users/{user_id}.json'):
                with open(f'users/{user_id}.json', 'r') as f:
                    return json.load(f)
        except:
            pass
        return []

    def save_user_account(self, user_id, account):
        try:
            os.makedirs('users', exist_ok=True)
            accounts = self.get_user_accounts(user_id)
            
            # Update existing or add new
            found = False
            for i, acc in enumerate(accounts):
                if acc['phone_number'] == account['phone_number']:
                    accounts[i] = account
                    found = True
                    break
            
            if not found:
                accounts.append(account)
            
            with open(f'users/{user_id}.json', 'w') as f:
                json.dump(accounts, f)
        except Exception as e:
            logger.error(f"Save account error: {e}")

    def save_user_api_key(self, user_id, api_key):
        try:
            os.makedirs('users', exist_ok=True)
            with open(f'users/{user_id}_apikey.txt', 'w') as f:
                f.write(api_key)
        except Exception as e:
            logger.error(f"Save API key error: {e}")

    def get_user_api_key(self, user_id):
        try:
            if os.path.exists(f'users/{user_id}_apikey.txt'):
                with open(f'users/{user_id}_apikey.txt', 'r') as f:
                    return f.read().strip()
        except:
            pass
        return None

    def run(self):
        self.application.run_polling()

# ========== PAYMENT FUNCTIONS ========== #

def get_qris_code(api_key: str, tokens: dict, transaction_id: str):
    path = "payments/api/v8/pending-detail"
    payload = {
        "transaction_id": transaction_id,
        "is_enterprise": False,
        "lang": "en",
        "status": ""
    }
    
    res = send_api_request(api_key, path, payload, tokens["id_token"], "POST")
    if res.get("status") != "SUCCESS":
        logger.error(f"Failed to fetch QRIS code: {res}")
        return None
    
    return res["data"].get("qr_code")

def settlement_qris(api_key: str, tokens: dict, token_payment: str, ts_to_sign: int, 
                   payment_target: str, price: int, item_name: str = ""):
    path = "payments/api/v8/settlement-qris"
    
    payload = {
        "total_discount": 0,
        "is_enterprise": False,
        "payment_token": "",
        "token_payment": token_payment,
        "activated_autobuy_code": "",
        "cc_payment_type": "",
        "is_myxl_wallet": False,
        "pin": "",
        "ewallet_promo_id": "",
        "members": [],
        "total_fee": 0,
        "fingerprint": "",
        "autobuy_threshold_setting": {
            "label": "",
            "type": "",
            "value": 0
        },
        "is_use_point": False,
        "lang": "en",
        "payment_method": "QRIS",
        "timestamp": ts_to_sign,
        "points_gained": 0,
        "can_trigger_rating": False,
        "akrab_members": [],
        "akrab_parent_alias": "",
        "referral_unique_code": "",
        "coupon": "",
        "payment_for": "BUY_PACKAGE",
        "with_upsell": False,
        "topup_number": "",
        "stage_token": "",
        "authentication_id": "",
        "encrypted_payment_token": build_encrypted_field(urlsafe_b64=True),
        "token": "",
        "token_confirmation": "",
        "access_token": tokens["access_token"],
        "wallet_number": "",
        "encrypted_authentication_id": build_encrypted_field(urlsafe_b64=True),
        "additional_data": {},
        "total_amount": price,
        "is_using_autobuy": False,
        "items": [{
            "item_code": payment_target,
            "product_type": "",
            "item_price": price,
            "item_name": item_name,
            "tax": 0
        }]
    }
    
    # Encrypt and sign the payload
    encrypted_payload = encryptsign_xdata(
        api_key=api_key,
        method="POST",
        path=path,
        id_token=tokens["id_token"],
        payload=payload
    )
    
    xtime = int(encrypted_payload["encrypted_body"]["xtime"])
    sig_time_sec = (xtime // 1000)
    
    # Prepare headers
    headers = {
        "host": "api.myxl.xlaxiata.co.id",
        "content-type": "application/json; charset=utf-8",
        "user-agent": "myXL / 8.6.0(1179); com.android.vending; (samsung; SM-N935F; SDK 33; Android 13)",
        "x-api-key": API_KEY,
        "authorization": f"Bearer {tokens['id_token']}",
        "x-hv": "v3",
        "x-signature-time": str(sig_time_sec),
        "x-signature": get_x_signature_payment(
            api_key,
            tokens["access_token"],
            ts_to_sign,
            payment_target,
            token_payment,
            "QRIS"
        ),
        "x-request-id": str(uuid.uuid4()),
        "x-request-at": java_like_timestamp(datetime.now()),
        "x-version-app": "8.6.0",
    }
    
    # Send request
    url = f"{BASE_URL}/{path}"
    response = requests.post(url, headers=headers, json=encrypted_payload["encrypted_body"], timeout=30)
    
    # Decrypt response
    try:
        decrypted_body = decrypt_xdata(api_key, response.json())
        if decrypted_body.get("status") == "SUCCESS":
            return decrypted_body["data"].get("transaction_id")
        return None
    except:
        return None

def settlement_bounty(api_key: str, tokens: dict, token_confirmation: str, ts_to_sign: int,
                     payment_target: str, price: int, item_name: str = ""):
    path = "api/v8/personalization/bounties-exchange"
    
    payload = {
        "total_discount": 0,
        "is_enterprise": False,
        "payment_token": "",
        "token_payment": "",
        "activated_autobuy_code": "",
        "cc_payment_type": "",
        "is_myxl_wallet": False,
        "pin": "",
        "ewallet_promo_id": "",
        "members": [],
        "total_fee": 0,
        "fingerprint": "",
        "autobuy_threshold_setting": {
            "label": "",
            "type": "",
            "value": 0
        },
        "is_use_point": False,
        "lang": "en",
        "payment_method": "BOUNTY",
        "timestamp": ts_to_sign,
        "points_gained": 0,
        "can_trigger_rating": False,
        "akrab_members": [],
        "akrab_parent_alias": "",
        "referral_unique_code": "",
        "coupon": "",
        "payment_for": "REDEEM_VOUCHER",
        "with_upsell": False,
        "topup_number": "",
        "stage_token": "",
        "authentication_id": "",
        "encrypted_payment_token": build_encrypted_field(urlsafe_b64=True),
        "token": "",
        "token_confirmation": token_confirmation,
        "access_token": tokens["access_token"],
        "wallet_number": "",
        "encrypted_authentication_id": build_encrypted_field(urlsafe_b64=True),
        "additional_data": {
            "original_price": price,
            "is_spend_limit_temporary": False,
            "migration_type": "",
            "akrab_m2m_group_id": "",
            "spend_limit_amount": 0,
            "is_spend_limit": False,
            "mission_id": "",
            "tax": 0,
            "benefit_type": "",
            "quota_bonus": 0,
            "cashtag": "",
            "is_family_plan": False,
            "combo_details": [],
            "is_switch_plan": False,
            "discount_recurring": 0,
            "is_akrab_m2m": False,
            "balance_type": "",
            "has_bonus": False,
            "discount_promo": 0
        },
        "total_amount": 0,
        "is_using_autobuy": False,
        "items": [{
            "item_code": payment_target,
            "product_type": "",
            "item_price": price,
            "item_name": item_name,
            "tax": 0
        }]
    }
    
    # Encrypt and sign the payload
    encrypted_payload = encryptsign_xdata(
        api_key=api_key,
        method="POST",
        path=path,
        id_token=tokens["id_token"],
        payload=payload
    )
    
    xtime = int(encrypted_payload["encrypted_body"]["xtime"])
    sig_time_sec = (xtime // 1000)
    
    # Get signature for bounty
    x_sig = get_x_signature_bounty(
        api_key,
        tokens["access_token"],
        ts_to_sign,
        payment_target,
        token_confirmation
    )
    
    # Prepare headers
    headers = {
        "host": "api.myxl.xlaxiata.co.id",
        "content-type": "application/json; charset=utf-8",
        "user-agent": "myXL / 8.6.0(1179); com.android.vending; (samsung; SM-N935F; SDK 33; Android 13)",
        "x-api-key": API_KEY,
        "authorization": f"Bearer {tokens['id_token']}",
        "x-hv": "v3",
        "x-signature-time": str(sig_time_sec),
        "x-signature": x_sig,
        "x-request-id": str(uuid.uuid4()),
        "x-request-at": java_like_timestamp(datetime.now()),
        "x-version-app": "8.6.0",
    }
    
    # Send request
    url = f"{BASE_URL}/{path}"
    response = requests.post(url, headers=headers, json=encrypted_payload["encrypted_body"], timeout=30)
    
    # Decrypt response
    try:
        decrypted_body = decrypt_xdata(api_key, response.json())
        return decrypted_body
    except:
        return response.json()

# ========== ORIGINAL MYXL FUNCTIONS ========== #

def validate_contact(contact: str) -> bool:
    if not contact.startswith("628") or len(contact) > 14:
        return False
    return True

def get_otp(contact: str) -> str:
    if not validate_contact(contact):
        raise ValueError("Invalid contact number")
    
    url = "https://gede.ciam.xlaxiata.co.id/realms/xl-ciam/auth/otp"
    params = {"contact": contact, "contactType": "SMS", "alternateContact": "false"}
    
    now = datetime.now(timezone(timedelta(hours=7)))
    ax_request_at = java_like_timestamp(now)
    ax_request_id = str(uuid.uuid4())

    headers = {
        "Accept-Encoding": "gzip, deflate, br",
        "Authorization": "Basic OWZjOTdlZDEtNmEzMC00OGQ1LTk1MTYtNjBjNTNjZTNhMTM1OllEV21GNExKajlYSUt3UW56eTJlMmxiMHRKUWIyOW8z",
        "Ax-Device-Id": "92fb44c0804233eb4d9e29f838223a14",
        "Ax-Fingerprint": "YmQLy9ZiLLBFAEVcI4Dnw9+NJWZcdGoQyewxMF/9hbfk/8GbKBgtZxqdiiam8+m2lK31E/zJQ7kjuPXpB3EE8naYL0Q8+0WLhFV1WAPl9Eg=",
        "Ax-Request-At": ax_request_at,
        "Ax-Request-Device": "samsung",
        "Ax-Request-Device-Model": "SM-N935F",
        "Ax-Request-Id": ax_request_id,
        "Ax-Substype": "PREPAID",
        "Content-Type": "application/json",
        "Host": "gede.ciam.xlaxiata.co.id",
        "User-Agent": "myXL / 8.6.0(1179); com.android.vending; (samsung; SM-N935F; SDK 33; Android 13)"
    }

    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    
    json_body = response.json()
    if "subscriber_id" not in json_body:
        raise ValueError("Subscriber ID not found in response")
    
    return json_body["subscriber_id"]

def submit_otp(api_key: str, contact: str, code: str):
    if not validate_contact(contact):
        raise ValueError("Invalid contact number")
    
    if not code or len(code) != 6:
        raise ValueError("Invalid OTP code")

    url = "https://gede.ciam.xlaxiata.co.id/realms/xl-ciam/protocol/openid-connect/token"

    now_gmt7 = datetime.now(timezone(timedelta(hours=7)))
    ts_for_sign = ts_gmt7_without_colon(now_gmt7)
    ts_header = ts_gmt7_without_colon(now_gmt7 - timedelta(minutes=5))
    signature = ax_api_signature(api_key, ts_for_sign, contact, code, "SMS")

    payload = f"contactType=SMS&code={code}&grant_type=password&contact={contact}&scope=openid"

    headers = {
        "Accept-Encoding": "gzip, deflate, br",
        "Authorization": "Basic OWZjOTdlZDEtNmEzMC00OGQ1LTk1MTYtNjBjNTNjZTNhMTM1OllEV21GNExKajlYSUt3UW56eTJlMmxiMHRKUWIyOW8z",
        "Ax-Api-Signature": signature,
        "Ax-Device-Id": "92fb44c0804233eb4d9e29f838223a14",
        "Ax-Fingerprint": "YmQLy9ZiLLBFAEVcI4Dnw9+NJWZcdGoQyewxMF/9hbfk/8GbKBgtZxqdiiam8+m2lK31E/zJQ7kjuPXpB3EE8naYL0Q8+0WLhFV1WAPl9Eg=",
        "Ax-Request-At": ts_header,
        "Ax-Request-Device": "samsung",
        "Ax-Request-Device-Model": "SM-N935F",
        "Ax-Request-Id": str(uuid.uuid4()),
        "Ax-Substype": "PREPAID",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "myXL / 8.6.0(1179); com.android.vending; (samsung; SM-N935F; SDK 33; Android 13)",
    }

    response = requests.post(url, data=payload, headers=headers, timeout=30)
    response.raise_for_status()
    
    json_body = response.json()
    if "error" in json_body:
        raise ValueError(f"OTP submission failed: {json_body['error_description']}")
    
    return json_body

def get_profile(api_key: str, access_token: str, id_token: str):
    path = "api/v8/profile"
    payload = {
        "access_token": access_token,
        "app_version": "8.6.0",
        "is_enterprise": False,
        "lang": "en"
    }
    
    response = send_api_request(api_key, path, payload, id_token, "POST")
    return response.get("data")

def get_balance(api_key: str, id_token: str):
    path = "api/v8/packages/balance-and-credit"
    payload = {
        "is_enterprise": False,
        "lang": "en"
    }
    
    response = send_api_request(api_key, path, payload, id_token, "POST")
    if "data" in response and "balance" in response["data"]:
        return response["data"]["balance"]
    raise ValueError("Failed to get balance")

def fetch_my_packages(api_key: str, tokens: dict):
    path = "api/v8/packages/quota-details"
    payload = {
        "is_enterprise": False,
        "lang": "en",
        "family_member_id": ""
    }
    
    response = send_api_request(api_key, path, payload, tokens["id_token"], "POST")
    if response.get("status") != "SUCCESS":
        raise ValueError("Failed to fetch packages")
    
    quotas = response["data"]["quotas"]
    packages = []
    
    for quota in quotas:
        try:
            package_details = get_package(api_key, tokens, quota["quota_code"])
            packages.append({
                "name": quota["name"],
                "quota_code": quota["quota_code"],
                "group_code": quota["group_code"],
                "family_code": package_details["package_family"]["package_family_code"] if package_details else "N/A"
            })
        except:
            packages.append({
                "name": quota["name"],
                "quota_code": quota["quota_code"],
                "group_code": quota["group_code"],
                "family_code": "N/A"
            })
    
    return packages

def get_package(api_key: str, tokens: dict, package_option_code: str):
    path = "api/v8/xl-stores/options/detail"
    payload = {
        "is_transaction_routine": False,
        "migration_type": "",
        "package_family_code": "",
        "family_role_hub": "",
        "is_autobuy": False,
        "is_enterprise": False,
        "is_shareable": False,
        "is_migration": False,
        "lang": "en",
        "package_option_code": package_option_code,
        "is_upsell_pdp": False,
        "package_variant_code": ""
    }
    
    response = send_api_request(api_key, path, payload, tokens["id_token"], "POST")
    if "data" not in response:
        raise ValueError("Failed to get package details")
    return response["data"]

def get_package_xut(api_key: str, tokens: dict):
    PACKAGE_FAMILY_CODE = "08a3b1e6-8e78-4e45-a540-b40f06871cfe"
    data = get_family(api_key, tokens, PACKAGE_FAMILY_CODE)
    if not data:
        return []
    
    packages = []
    start_number = 1
    
    for variant in data["package_variants"]:
        for option in variant["package_options"]:
            friendly_name = option["name"]
            if friendly_name.lower() == "vidio":
                friendly_name = "Unli Turbo Vidio"
            if friendly_name.lower() == "iflix":
                friendly_name = "Unli Turbo Iflix"
                
            packages.append({
                "number": start_number,
                "name": friendly_name,
                "price": option["price"],
                "code": option["package_option_code"]
            })
            start_number += 1
            
    return packages

def get_packages_by_family(api_key: str, tokens: dict, family_code: str):
    data = get_family(api_key, tokens, family_code)
    if not data:
        return []
    
    packages = []
    option_number = 1
    
    for variant in data["package_variants"]:
        for option in variant["package_options"]:
            packages.append({
                "number": option_number,
                "name": option["name"],
                "price": option["price"],
                "code": option["package_option_code"]
            })
            option_number += 1
            
    return packages

def get_family(api_key: str, tokens: dict, family_code: str):
    path = "api/v8/xl-stores/options/list"
    payload = {
        "is_show_tagging_tab": True,
        "is_dedicated_event": True,
        "is_transaction_routine": False,
        "migration_type": "NONE",
        "package_family_code": family_code,
        "is_autobuy": False,
        "is_enterprise": False,
        "is_pdlp": True,
        "referral_code": "",
        "is_migration": False,
        "lang": "en"
    }
    
    response = send_api_request(api_key, path, payload, tokens["id_token"], "POST")
    if response.get("status") != "SUCCESS":
        raise ValueError("Failed to get family data")
    return response["data"]

def purchase_package(api_key: str, tokens: dict, package_option_code: str):
    package_details = get_package(api_key, tokens, package_option_code)
    if not package_details:
        raise ValueError("Failed to get package details")
    
    token_confirmation = package_details["token_confirmation"]
    payment_target = package_details["package_option"]["package_option_code"]
    
    # Get payment methods
    payment_methods = get_payment_methods(api_key, tokens, token_confirmation, payment_target)
    if not payment_methods:
        raise ValueError("Failed to get payment methods")
    
    token_payment = payment_methods["token_payment"]
    ts_to_sign = payment_methods["timestamp"]
    
    # Process payment with balance
    result = settlement_balance(
        api_key,
        tokens,
        token_payment,
        ts_to_sign,
        payment_target,
        package_details["package_option"]["price"],
        package_details["package_option"]["name"]
    )
    
    return result

def get_payment_methods(api_key: str, tokens: dict, token_confirmation: str, payment_target: str):
    path = "payments/api/v8/payment-methods-option"
    payload = {
        "payment_type": "PURCHASE",
        "is_enterprise": False,
        "payment_target": payment_target,
        "lang": "en",
        "is_referral": False,
        "token_confirmation": token_confirmation
    }
    
    response = send_api_request(api_key, path, payload, tokens["id_token"], "POST")
    if response.get("status") != "SUCCESS":
        raise ValueError("Failed to get payment methods")
    return response["data"]

def settlement_balance(api_key: str, tokens: dict, token_payment: str, ts_to_sign: int, 
                      payment_target: str, price: int, item_name: str):
    path = "payments/api/v8/settlement-balance"
    
    payload = {
        "total_discount": 0,
        "is_enterprise": False,
        "payment_token": "",
        "token_payment": token_payment,
        "activated_autobuy_code": "",
        "cc_payment_type": "",
        "is_myxl_wallet": False,
        "pin": "",
        "ewallet_promo_id": "",
        "members": [],
        "total_fee": 0,
        "fingerprint": "",
        "autobuy_threshold_setting": {
            "label": "",
            "type": "",
            "value": 0
        },
        "is_use_point": False,
        "lang": "en",
        "payment_method": "BALANCE",
        "timestamp": ts_to_sign,
        "points_gained": 0,
        "can_trigger_rating": False,
        "akrab_members": [],
        "akrab_parent_alias": "",
        "referral_unique_code": "",
        "coupon": "",
        "payment_for": "BUY_PACKAGE",
        "with_upsell": False,
        "topup_number": "",
        "stage_token": "",
        "authentication_id": "",
        "encrypted_payment_token": build_encrypted_field(urlsafe_b64=True),
        "token": "",
        "token_confirmation": "",
        "access_token": tokens["access_token"],
        "wallet_number": "",
        "encrypted_authentication_id": build_encrypted_field(urlsafe_b64=True),
        "additional_data": {},
        "total_amount": price,
        "is_using_autobuy": False,
        "items": [{
            "item_code": payment_target,
            "product_type": "",
            "item_price": price,
            "item_name": item_name,
            "tax": 0
        }]
    }
    
    # Encrypt and sign the payload
    encrypted_payload = encryptsign_xdata(
        api_key=api_key,
        method="POST",
        path=path,
        id_token=tokens["id_token"],
        payload=payload
    )
    
    xtime = int(encrypted_payload["encrypted_body"]["xtime"])
    sig_time_sec = (xtime // 1000)
    
    # Get signature for payment
    x_sig = get_x_signature_payment(
        api_key,
        tokens["access_token"],
        ts_to_sign,
        payment_target,
        token_payment,
        "BALANCE"
    )
    
    # Prepare headers
    headers = {
        "host": "api.myxl.xlaxiata.co.id",
        "content-type": "application/json; charset=utf-8",
        "user-agent": "myXL / 8.6.0(1179); com.android.vending; (samsung; SM-N935F; SDK 33; Android 13)",
        "x-api-key": API_KEY,
        "authorization": f"Bearer {tokens['id_token']}",
        "x-hv": "v3",
        "x-signature-time": str(sig_time_sec),
        "x-signature": x_sig,
        "x-request-id": str(uuid.uuid4()),
        "x-request-at": java_like_timestamp(datetime.now()),
        "x-version-app": "8.6.0",
    }
    
    # Send request
    url = f"{BASE_URL}/{path}"
    response = requests.post(url, headers=headers, json=encrypted_payload["encrypted_body"], timeout=30)
    
    # Decrypt response
    try:
        decrypted_body = decrypt_xdata(api_key, response.json())
        return decrypted_body
    except:
        return response.json()

def send_api_request(api_key: str, path: str, payload_dict: dict, id_token: str, method: str = "POST"):
    encrypted_payload = encryptsign_xdata(
        api_key=api_key,
        method=method,
        path=path,
        id_token=id_token,
        payload=payload_dict
    )
    
    xtime = int(encrypted_payload["encrypted_body"]["xtime"])
    sig_time_sec = (xtime // 1000)

    body = encrypted_payload["encrypted_body"]
    x_sig = encrypted_payload["x_signature"]
    
    headers = {
        "host": "api.myxl.xlaxiata.co.id",
        "content-type": "application/json; charset=utf-8",
        "user-agent": "myXL / 8.6.0(1179); com.android.vending; (samsung; SM-N935F; SDK 33; Android 13)",
        "x-api-key": API_KEY,
        "authorization": f"Bearer {id_token}",
        "x-hv": "v3",
        "x-signature-time": str(sig_time_sec),
        "x-signature": x_sig,
        "x-request-id": str(uuid.uuid4()),
        "x-request-at": java_like_timestamp(datetime.now()),
        "x-version-app": "8.6.0",
    }

    url = f"{BASE_URL}/{path}"
    response = requests.post(url, headers=headers, json=body, timeout=30)

    try:
        decrypted_body = decrypt_xdata(api_key, response.json())
        return decrypted_body
    except:
        return response.json()

def verify_api_key(api_key: str) -> bool:
    """
    Verify API key with external service
    """
    try:
        url = f"https://crypto.mashu.lol/api/verify?key={api_key}"
        response = requests.get(url, timeout=10.0)
        return response.status_code == 200
    except:
        return False

def get_new_token(refresh_token: str):
    """Get new tokens using refresh token"""
    try:
        now = datetime.now()
        ax_request_at = java_like_timestamp(now)
        
        response = requests.post(
            'https://gede.ciam.xlaxiata.co.id/realms/xl-ciam/protocol/openid-connect/token',
            f'grant_type=refresh_token&refresh_token={refresh_token}',
            headers={
                'Host': 'gede.ciam.xlaxiata.co.id',
                'ax-request-at': ax_request_at,
                'ax-device-id': '92fb44c0804233eb4d9e29f838223a15',
                'ax-request-id': str(uuid.uuid4()),
                'ax-request-device': 'samsung',
                'ax-request-device-model': 'SM-N935F',
                'ax-fingerprint': 'YmQLy9ZiLLBFAEVcI4Dnw9+NJWZcdGoQyewxMF/9hbfk/8GbKBgtZxqdiiam8+m2lK31E/zJQ7kjuPXpB3EE8uHGk5i+PevKLaUFo/Xi5Fk=',
                'authorization': 'Basic OWZjOTdlZDEtNmEzMC00OGQ1LTk1MTYtNjBjNTNjZTNahMTM1OllEV21GNExKajlYSUt3UW56eTJlMmxiMHRKUWIyOW8z',
                'user-agent': 'myXL / 8.6.0(1179); com.android.vending; (samsung; SM-N935F; SDK 33; Android 13)',
                'ax-substype': 'PREPAID',
                'content-type': 'application/x-www-form-urlencoded'
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Refresh token failed: {response.text}")
    except Exception as e:
        logger.error(f"Get new token error: {e}")
        raise

# Main execution
if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN not found in environment variables")
        print("💡 Create a .env file with: BOT_TOKEN=your_bot_token")
        exit(1)
    
    # Create users directory if not exists
    os.makedirs("users", exist_ok=True)
    
    # Start the bot
    bot = MyXLBot(BOT_TOKEN)
    print("🤖 MyXL Telegram Bot started...")

    bot.run()

