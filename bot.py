from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ------------------ Conversation States ------------------
LOGIN_USERNAME, LOGIN_PASSWORD = range(2)
REGISTER_NAME, REGISTER_EMAIL = range(2)

# ------------------ Start Handler ------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Welcome to RunMaxPayBot! Use /login or /register to proceed.")

# ------------------ Login Flow ------------------
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔐 Please enter your username:")
    return LOGIN_USERNAME

async def get_login_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["username"] = update.message.text
    await update.message.reply_text("🔐 Enter your password:")
    return LOGIN_PASSWORD

async def get_login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Replace this logic with actual DB validation
    context.user_data["password"] = update.message.text
    await update.message.reply_text("✅ Login successful! Welcome.")
    return ConversationHandler.END

# ------------------ Register Flow ------------------
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👤 Please enter your full name:")
    return REGISTER_NAME

async def get_register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("📧 Now enter your email address:")
    return REGISTER_EMAIL

async def get_register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    # Save data to DB here if needed
    await update.message.reply_text("✅ Registration complete! You can now /login.")
    return ConversationHandler.END

# ------------------ Cancel Command ------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END

# ------------------ Main ------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    login_conv = ConversationHandler(
        entry_points=[CommandHandler("login", login)],
        states={
            LOGIN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_login_username)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_login_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    register_conv = ConversationHandler(
        entry_points=[CommandHandler("register", register)],
        states={
            REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_register_name)],
            REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_register_email)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(login_conv)
    app.add_handler(register_conv)
    app.add_handler(CommandHandler("cancel", cancel))

    app.run_polling()

if __name__ == "__main__":
    main()
