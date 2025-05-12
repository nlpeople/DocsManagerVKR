from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import sync_to_async
from Docs.models import Profile, DocumentFile, DocumentComment, User
from dotenv import load_dotenv
import logging
import asyncio

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8021983986:AAEAd83O01vWEGJBVsp0_DA4tNxvpG9Tdp8"
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


# Обработчики команд бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    username = update.effective_user.username
    logger.info(f"Пользователь {telegram_id} (@{username}) использовал /start")

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
def get_user_by_id(user_id):
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return None


@sync_to_async
def get_user_name(user):
    if not user:
        return "unknown"
    return user.get_full_name() or user.username


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка в боте: {context.error}", exc_info=True)
    if update.effective_message:
        await update.effective_message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")


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

            # Используем асинхронный метод для получения username
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


# Уведомления
async def send_telegram_notification(profile, message):
    try:
        if profile.telegram_id:
            await application.bot.send_message(
                chat_id=profile.telegram_id,
                text=message
            )
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения для профиля {profile.id}: {e}", exc_info=True)


@receiver(post_save, sender=DocumentFile)
def notify_file_change(sender, instance, created, **kwargs):
    async def wrapper():
        try:
            creators = await sync_to_async(list)(instance.document.creators.all())
            for creator in creators:
                profile = await sync_to_async(getattr)(creator, 'profile', None)
                if profile and profile.telegram_id:
                    user_name = await get_user_name(creator)
                    message = f"📄 Файл {'добавлен' if created else 'изменен'} в документе {instance.document.title}\n"
                    message += f"Файл: {instance.name}"
                    await send_telegram_notification(profile, message)
        except Exception as e:
            logger.error(f"Ошибка в обработчике файлов: {e}", exc_info=True)

    asyncio.run_coroutine_threadsafe(wrapper(), application.job_queue._dispatcher._event_loop)

@receiver(post_save, sender=DocumentComment)
def notify_new_comment(sender, instance, created, **kwargs):
    if not created:
        return

    async def wrapper():
        creators = await get_document_creators(instance.document_id)
        for creator in creators:
            if creator.id != instance.user.id and hasattr(creator, 'profile'):
                message = f"💬 Новый комментарий в документе {instance.document.title}\n"
                message += f"От: {instance.user.get_full_name() or instance.user.username}\n"
                message += f"Текст: {instance.message[:100]}..."
                await send_telegram_notification(creator.profile, message)

    asyncio.run_coroutine_threadsafe(wrapper(), application.job_queue._dispatcher._event_loop)


def start_bot_logic():
    global application
    logger.info("🚀 Telegram-бот запускается...")
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", bind_telegram))
    application.add_handler(CallbackQueryHandler(unbind_telegram, pattern='^unbind_telegram$'))

    logger.info("✅ Бот успешно запущен и слушает обновления.")
    application.run_polling()


if __name__ == "__main__":
    start_bot_logic()