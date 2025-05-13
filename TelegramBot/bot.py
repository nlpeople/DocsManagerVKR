from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import sync_to_async
from Docs.models import Profile, DocumentFile, DocumentComment, User
from dotenv import load_dotenv
import logging
import asyncio
import os

load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
application = None

# Асинхронные методы для работы с БД
async def get_profile_by_code(code: str):
    try:
        return await Profile.objects.aget(telegram_token=code)
    except Profile.DoesNotExist:
        return None

async def get_profile_by_telegram_id(telegram_id: str):
    try:
        return await Profile.objects.aget(telegram_id=telegram_id)
    except Profile.DoesNotExist:
        return None

async def save_profile(profile: Profile):
    await profile.asave()

async def get_document_creators(document_id):
    from Docs.models import Document
    try:
        document = await Document.objects.aget(pk=document_id)
        return [creator async for creator in document.creators.all()]
    except Document.DoesNotExist:
        return []

async def send_telegram_notification(telegram_id: str, message: str):
    """Отправляет уведомление в Telegram по telegram_id."""
    try:
        await application.bot.send_message(chat_id=telegram_id, text=message)
        logger.info(f"Уведомление отправлено пользователю с telegram_id {telegram_id}: {message}")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления пользователю с telegram_id {telegram_id}: {str(e)}")

# Обработчики команд бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    username = update.effective_user.username
    args = context.args
    logger.info(f"Пользователь {telegram_id} (@{username}) использовал /start с аргументами: {args}")

    if args:
        # Если передан код, обрабатываем как привязку
        await bind_telegram(update, context)
    else:
        profile = await get_profile_by_telegram_id(telegram_id)
        if profile:
            keyboard = [[InlineKeyboardButton("Отвязать Telegram", callback_data='unbind_telegram')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Ваш Telegram аккаунт уже привязан. Вы можете его отвязать.",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "Ваш Telegram аккаунт не привязан.\nПерейдите по ссылке на сайте, чтобы выполнить привязку."
            )

@sync_to_async
def get_user_username(user_id):
    try:
        user = User.objects.get(pk=user_id)
        return user.username
    except User.DoesNotExist:
        return "unknown"

async def bind_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    username = update.effective_user.username
    args = context.args

    if args:
        code = args[0]
        logger.info(f"Пользователь {telegram_id} (@{username}) пытается привязаться с кодом {code}")
        profile = await get_profile_by_code(code)

        if profile:
            if profile.telegram_id:
                await update.message.reply_text("Этот код уже был использован.")
                logger.warning(f"Попытка повторной привязки к уже использованному коду: {code}")
                return

            existing = await get_profile_by_telegram_id(telegram_id)
            if existing:
                await update.message.reply_text("Этот Telegram уже привязан к другому аккаунту.")
                logger.warning(f"Telegram ID {telegram_id} уже привязан к другому профилю.")
                return

            profile.telegram_id = telegram_id
            profile.telegram_token = None
            await save_profile(profile)

            user_username = await get_user_username(profile.user_id)
            logger.info(f"Telegram ID {telegram_id} привязан к пользователю {user_username}")

            await update.message.reply_text("✅ Привязка выполнена успешно!")
        else:
            await update.message.reply_text("⛔ Неверный код привязки или он уже использован.")
            logger.warning(f"Неверный код привязки: {code}")
    else:
        await update.message.reply_text("Используйте специальную ссылку с кодом, чтобы привязать аккаунт.")
        logger.info(f"Пользователь {telegram_id} не передал код.")

async def unbind_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    username = update.effective_user.username
    profile = await get_profile_by_telegram_id(telegram_id)

    if profile:
        profile.telegram_id = None
        await save_profile(profile)
        await update.callback_query.answer("Telegram отвязан.")
        await update.callback_query.edit_message_text("Ваш Telegram аккаунт успешно отвязан.")
        logger.info(f"Пользователь {telegram_id} (@{username}) отвязал Telegram")
    else:
        await update.callback_query.answer("Telegram не был привязан.")
        logger.warning(f"Попытка отвязки несуществующего Telegram ID: {telegram_id}")

def start_bot_logic():
    global application
    logger.info("🚀 Telegram-бот запускается...")
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("bind", bind_telegram))
    application.add_handler(CallbackQueryHandler(unbind_telegram, pattern='^unbind_telegram$'))

    logger.info("✅ Бот успешно запущен и слушает обновления.")
    application.run_polling()

if __name__ == "__main__":
    start_bot_logic()