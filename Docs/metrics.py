from prometheus_client import Counter, Gauge, Histogram
from django.db.models import Count
from .models import Document, Profile, DocumentComment, DocumentFile, DocumentSignature, DocumentTemplate
from django.utils import timezone

# Метрики
# 1. Количество документов по статусам
document_status_gauge = Gauge(
    'documents_by_status',
    'Number of documents by status',
    ['status']
)

# 2. Общее количество документов
total_documents_counter = Counter(
    'total_documents_created',
    'Total number of documents created'
)

# 3. Количество подписанных документов
signed_documents_counter = Counter(
    'signed_documents_total',
    'Total number of signed documents'
)

# 4. Количество неподписанных документов
unsigned_documents_gauge = Gauge(
    'unsigned_documents',
    'Number of documents waiting for signatures'
)

# 5. Количество пользователей по ролям
users_by_role_gauge = Gauge(
    'users_by_role',
    'Number of users by role',
    ['role']
)

# 6. Количество комментариев
total_comments_counter = Counter(
    'total_document_comments',
    'Total number of comments added to documents'
)

# 7. Количество загруженных файлов
total_files_counter = Counter(
    'total_document_files',
    'Total number of files uploaded'
)

# 8. Среднее время подписания документа
signing_time_histogram = Histogram(
    'document_signing_duration_seconds',
    'Time taken to fully sign a document',
    buckets=(60, 300, 600, 1800, 3600, 7200, 86400, float("inf"))
)

# 9. Количество активных Telegram-привязок
telegram_bind_gauge = Gauge(
    'telegram_linked_users',
    'Number of users with linked Telegram accounts'
)

# 10. Количество шаблонов документов по типам
template_by_type_gauge = Gauge(
    'document_templates_by_type',
    'Number of document templates by type',
    ['document_type']
)

def update_metrics():
    """Обновляет значения всех метрик на основе текущих данных."""
    # 1. Документы по статусам
    status_counts = Document.objects.values('status').annotate(count=Count('id'))
    for status in Document.STATUS_CHOICES:
        status_value = status[0]
        count = next((item['count'] for item in status_counts if item['status'] == status_value), 0)
        document_status_gauge.labels(status=status_value).set(count)

    # 2. Общее количество документов
    total_documents = Document.objects.count()
    total_documents_counter.inc(total_documents - total_documents_counter._value.get())

    # 3. Подписанные документы
    signed_documents = Document.objects.filter(status='signed').count()
    signed_documents_counter.inc(signed_documents - signed_documents_counter._value.get())

    # 4. Неподписанные документы
    unsigned_documents = Document.objects.filter(status='pending').count()
    unsigned_documents_gauge.set(unsigned_documents)

    # 5. Пользователи по ролям
    role_counts = Profile.objects.values('role').annotate(count=Count('id'))
    for role in Profile.ROLE_CHOICES:
        role_value = role[0]
        count = next((item['count'] for item in role_counts if item['role'] == role_value), 0)
        users_by_role_gauge.labels(role=role_value).set(count)

    # 6. Количество комментариев
    total_comments = DocumentComment.objects.count()
    total_comments_counter.inc(total_comments - total_comments_counter._value.get())

    # 7. Количество файлов
    total_files = DocumentFile.objects.filter(status='uploaded').count()
    total_files_counter.inc(total_files - total_files_counter._value.get())

    # 8. Время подписания документов
    signed_docs = Document.objects.filter(status='signed')
    for doc in signed_docs:
        if doc.signatures.exists():
            last_signature = doc.signatures.order_by('-signed_at').first()
            if last_signature:
                duration = (last_signature.signed_at - doc.created_at).total_seconds()
                signing_time_histogram.observe(duration)

    # 9. Telegram-привязки
    telegram_linked = Profile.objects.exclude(telegram_id__isnull=True).count()
    telegram_bind_gauge.set(telegram_linked)

    # 10. Шаблоны документов по типам
    template_counts = DocumentTemplate.objects.values('document_type').annotate(count=Count('id'))
    for doc_type in DocumentTemplate.DOCUMENT_TYPES:
        doc_type_value = doc_type[0]
        count = next((item['count'] for item in template_counts if item['document_type'] == doc_type_value), 0)
        template_by_type_gauge.labels(document_type=doc_type_value).set(count)