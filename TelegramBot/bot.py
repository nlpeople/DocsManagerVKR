import os
import re
import django
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler, filters
from asgiref.sync import sync_to_async
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.settings import Settings
import chromadb
import requests
import logging
from pathlib import Path
import time

# Настройка Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DocsManage.settings")
django.setup()

from Docs.models import Profile

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8021983986:AAEAd83O01vWEGJBVsp0_DA4tNxvpG9Tdp8")

# Класс для индексации и поиска
class OptimizedIndexer:
    def __init__(self, ollama_model="qwen2.5:1.5b", docs_path="media/documents", index_path="storage", batch_size=32):
        self.ollama_model = ollama_model
        self.docs_path = Path(docs_path)
        self.index_path = Path(index_path)
        self.batch_size = batch_size

        logging.getLogger("chromadb").setLevel(logging.ERROR)
        self._check_ollama_availability()
        self._initialize_models()
        self._setup_chroma()

    def _check_ollama_availability(self, max_retries=3):
        for i in range(max_retries):
            try:
                response = requests.get("http://ollama:11434/api/tags", timeout=10)
                if response.status_code == 200:
                    try:
                        response.json()
                        print("✅ Сервер Ollama доступен")
                        return
                    except ValueError:
                        print("⚠️ Ответ от Ollama не в формате JSON")
                        return
            except requests.exceptions.RequestException as e:
                if i < max_retries - 1:
                    print(f"⚠️ Попытка {i + 1}/{max_retries}: {e}")
                    time.sleep(2)
                    continue
                raise ConnectionError("❌ Не удалось подключиться к серверу Ollama")

    def _initialize_models(self):
        self.llm = Ollama(
            model=self.ollama_model,
            base_url="http://ollama:11434",
            temperature=0.2,
            request_timeout=120.0,
            additional_kwargs={"num_thread": 8, "num_ctx": 4096, "timeout": 120}
        )
        self.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            embed_batch_size=32
        )
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model

    def _setup_chroma(self):
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.index_path),
            settings=chromadb.Settings(anonymized_telemetry=False, allow_reset=True)
        )
        self.collection = self.chroma_client.get_or_create_collection("default", metadata={"hnsw:space": "cosine"})
        self.vector_store = ChromaVectorStore(chroma_collection=self.collection)

    def create_or_load_index(self):
        if self.collection.count() > 0:
            print("🔄 Загрузка существующего индекса...")
            storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
            return load_index_from_storage(storage_context)

        print("📄 Индексация документов...")
        documents = SimpleDirectoryReader(str(self.docs_path), recursive=True).load_data()
        index = VectorStoreIndex.from_documents(documents, vector_store=self.vector_store, show_progress=True)
        index.storage_context.persist(persist_dir=str(self.index_path))
        return index

    async def query(self, question: str, similarity_top_k: int = 3, max_retries: int = 3):
        index = self.create_or_load_index()
        query_engine = index.as_query_engine(similarity_top_k=similarity_top_k)
        for attempt in range(max_retries):
            try:
                return query_engine.query(question)
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Попытка {attempt + 1}/{max_retries} не удалась: {str(e)}")
                    time.sleep(2)
                    continue
                raise

# Инициализация
indexer = OptimizedIndexer()

# Async-функции для базы данных
@sync_to_async
def get_profile_by_token(token):
    return Profile.objects.filter(telegram_token=token).first()

@sync_to_async
def save_profile(profile):
    profile.save()

@sync_to_async
def get_profile_by_telegram_id(telegram_id):
    return Profile.objects.filter(telegram_id=telegram_id).first()

@sync_to_async
def get_user_first_last_name(profile):
    if profile and profile.user:
        return f"{profile.user.first_name} {profile.user.last_name}"
    return None


# /start
async def start(update: Update, context: CallbackContext):
    telegram_id = str(update.effective_user.id)
    profile = await get_profile_by_telegram_id(telegram_id)

    if len(context.args) == 0:
        if profile:
            username = await get_user_first_last_name(profile)
            await update.message.reply_text(f"Привет, {username}! Аккаунт уже привязан.")
        else:
            await update.message.reply_text("Пожалуйста, перейдите на сайт и выполните привязку.")
        return

    token = context.args[0]
    profile = await get_profile_by_token(token)

    if profile:
        username = await get_user_first_last_name(profile)
        if not profile.telegram_id:
            profile.telegram_id = telegram_id
            profile.telegram_token = None
            await save_profile(profile)
            await update.message.reply_text(f"Привет, {username}! Telegram успешно привязан.")
        else:
            await update.message.reply_text(f"Привет, {username}! Telegram уже был привязан.")
    else:
        await update.message.reply_text("Неверный токен. Попробуйте снова.")

# /unlink
async def unlink(update: Update, context: CallbackContext):
    telegram_id = str(update.effective_user.id)
    profile = await get_profile_by_telegram_id(telegram_id)

    if profile:
        profile.telegram_id = None
        await save_profile(profile)
        await update.message.reply_text("Telegram отвязан от аккаунта.")
    else:
        await update.message.reply_text("Telegram не привязан к аккаунту.")

# Извлечение ключевых слов
def extract_keywords(text):
    text = text.lower() if isinstance(text, str) else str(text).lower()
    words = re.findall(r'\b\w+\b', text)
    stop_words = set([
        "и", "в", "на", "с", "по", "за", "для", "от", "до", "или", "но", "о", "об", "из", "при", "как", "что",
        "это", "то", "же", "бы", "быть", "а", "у", "не", "да", "нет"
    ])
    return {word for word in words if word not in stop_words and len(word) > 2}

# /ask
async def ask(update: Update, context: CallbackContext):
    telegram_id = str(update.effective_user.id)
    profile = await get_profile_by_telegram_id(telegram_id)

    if not profile:
        await update.message.reply_text("❌ Ваш Telegram не привязан. Перейдите на сайт и выполните привязку.")
        return

    if len(context.args) == 0:
        await update.message.reply_text("Используйте команду /ask <ваш вопрос>")
        return

    question = " ".join(context.args)

    try:
        waiting = await update.message.reply_text("⌛ Думаю над ответом...")
        response = await indexer.query(question)
        response_text = str(response.response)

        if not response_text or len(extract_keywords(response_text)) < 2:
            await update.message.reply_text("⚠️ Не удалось найти подходящий ответ.")
        else:
            await update.message.reply_text(response_text)

        await waiting.delete()
    except Exception as e:
        await update.message.reply_text("⚠️ Произошла ошибка при обработке запроса.")
        print(e)

# Обработка обычных сообщений
async def handle_message(update: Update, context: CallbackContext):
    await update.message.reply_text("Я вас не понял. Используйте команду /ask <ваш вопрос>.")

# Главный цикл бота
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("unlink", unlink))
    app.add_handler(CommandHandler("ask", ask))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
