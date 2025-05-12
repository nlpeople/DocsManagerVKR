# TelegramBot/management/commands/runbot.py

from django.core.management.base import BaseCommand
from TelegramBot.bot import start_bot_logic

class Command(BaseCommand):
    help = 'Run the Telegram bot'

    def handle(self, *args, **options):
        # Просто вызываем функцию, которая запускает бота
        start_bot_logic()
