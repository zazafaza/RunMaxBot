# runmaxpaybot.py
import os
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- DB Setup ---
db = sqlite3.connect("runmaxpay_users.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS merchants (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT,
        email TEXT,
        name TEXT,
        balance REAL DEFAULT 0,
        pending_balance REAL DEFAULT 0,
        two_fa_code TEXT
    )
''')
db.commit()

# --- States ---
REGISTER_NAME, REGISTER_EMAIL, REGISTER_USERNAME, REGISTER_PASSWORD, REGISTER_2FA = range(5)
LOGIN_USERNAME, LOGIN_PASSWORD, LOGIN_2FA = range(5, 8)

# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Login", callback_data="login")],
        [InlineKeyboardButton("Register", callback_data="register")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("\u2705 Welcome to RunMaxPayBot! Please choose:", reply_markup=reply_markup)

# --- Register Flow ---
async def register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Enter your full name:")
    return REGISTER_NAME

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Enter your email:")
    return REGISTER_EMAIL

async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    await update.message.reply_text("Choose a username:")
    return REGISTER_USERNAME

async def register_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["username"] = update.message.text
    await update.message.reply_text("Choose a password:")
    return REGISTER_PASSWORD

async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["password"] = update.message.text
    code = str(random.randint(100000, 999999))
    context.user_data["two_fa"] = code
    await update.message.reply_text(f"Your 2FA Code: {code}. Please enter it:")
    return REGISTER_2FA

async def register_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == context.user_data["two_fa"]:
        cursor.execute("""
            INSERT INTO merchants (telegram_id, username, password, email, name, two_fa_code)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            update.message.from_user.id,
            context.user_data["username"],
            context.user_data["password"],
            context.user_data["email"],
            context.user_data["name"],
            context.user_data["two_fa"]
        ))
        db.commit()
        await update.message.reply_text("\u2705 Registered successfully! Use /login to access your dashboard.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("\u274C Incorrect 2FA. Try again:")
        return REGISTER_2FA

# --- Login Flow ---
async def login_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Enter your username:")
    return LOGIN_USERNAME

async def login_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["login_username"] = update.message.text
    await update.message.reply_text("Enter your password:")
    return LOGIN_PASSWORD

async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["login_password"] = update.message.text
    await update.message.reply_text("Enter your 2FA code:")
    return LOGIN_2FA

async def login_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = context.user_data["login_username"]
    password = context.user_data["login_password"]
    code = update.message.text
    cursor.execute("SELECT name, balance, pending_balance FROM merchants WHERE username=? AND password=? AND two_fa_code=?",
                   (username, password, code))
    user = cursor.fetchone()
    if user:
        name, balance, pending = user
        await update.message.reply_text(f"\u2705 Welcome, {name}!")
        await dashboard(update, context, name, balance, pending)
        return ConversationHandler.END
    else:
        await update.message.reply_text("\u274C Login failed. Try again with /login.")
        return ConversationHandler.END

# --- Dashboard ---
async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE, name, balance, pending):
    keyboard = [
        [InlineKeyboardButton("Order Card", callback_data="order_card")],
        [InlineKeyboardButton("My Cards", callback_data="my_cards")],
        [InlineKeyboardButton("Transactions", callback_data="transactions")],
        [InlineKeyboardButton("Logout", callback_data="logout")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"\n\U0001F464 Name: {name}\n\n\U0001F4B0 Available: ${balance:.2f}\nPending: ${pending:.2f}",
        reply_markup=reply_markup
    )

# --- App Setup ---
app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
        CallbackQueryHandler(register_callback, pattern="^register$"),
        CallbackQueryHandler(login_callback, pattern="^login$")
    ],
    states={
        REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
        REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
        REGISTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_username)],
        REGISTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_password)],
        REGISTER_2FA: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_2fa)],

        LOGIN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_username)],
        LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
        LOGIN_2FA: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_2fa)],
    },
    fallbacks=[]
)

app.add_handler(conv_handler)
app.run_polling()
