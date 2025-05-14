from django.core.management.base import BaseCommand
import TelegramBot.bot as bot_module  # Импортируем наш bot.py как модуль

class Command(BaseCommand):
    help = "Запускает Telegram-бота"

    def handle(self, *args, **options):
        bot_module.main()  # вызываем main() из bot.py
