import secrets
from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from django.db import models
import hashlib
import json

from django.utils import timezone


class Profile(models.Model):
    # Связь с моделью пользователя
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Фамилия')
    photo = models.ImageField(upload_to='profile_pics/', blank=True, null=True, verbose_name='Фото профиля')

    # Роль пользователя
    ROLE_CHOICES = [
        ('employee', 'Сотрудник'),
        ('admin', 'Администратор'),
        ('director', 'Директор'),
        ('deputy_director', 'Заместитель директора'),
        ('secretary', 'Секретарь'),
    ]
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='employee')

    # Telegram ID (может быть пустым)
    telegram_id = models.CharField(max_length=100, blank=True, null=True)
    telegram_token = models.CharField(max_length=100, blank=True, null=True)  # Новое поле для токена

    def generate_telegram_token(self):
        self.telegram_token = secrets.token_urlsafe(16)  # Генерация случайного токена
        self.save()

    def clear_telegram_token(self):
        self.telegram_token = None
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Document(models.Model):
    # Статусы документа
    STATUS_CHOICES = [
        ('accept', 'Принят'),
        ('signed', 'Подписан'),
        ('pending', 'На подписании'),
        ('revision', 'На доработке'),
    ]

    # Основные поля
    title = models.CharField(max_length=255, verbose_name='Название документа')
    description = models.CharField(max_length=500, verbose_name='Описание документа', blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending', verbose_name='Статус документа')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    # Создатели документа (может быть несколько)
    creators = models.ManyToManyField(User, related_name='created_documents', verbose_name='Создатели')

    # Подписанты (пользователи, которые должны подписать документ)
    signers = models.ManyToManyField(User, related_name='documents_to_sign', verbose_name='Подписанты')

    # Пользователи, которые уже подписали документ
    signed_by = models.ManyToManyField(User, related_name='signed_documents', verbose_name='Подписавшие', blank=True)

    def add_signature(self, user, signature_data=None):
        """Добавляет электронную подпись пользователя"""
        if user not in self.signers.all():
            raise ValidationError("Пользователь не является подписантом этого документа")

        if self.signatures.filter(user=user).exists():
            raise ValidationError("Пользователь уже подписал этот документ")

        # Генерируем уникальную подпись на основе документа и пользователя
        signature_hash = self.generate_signature_hash(user)

        signature = DocumentSignature.objects.create(
            document=self,
            user=user,
            signature=signature_hash,
            signature_data=signature_data or {}
        )

        self.signed_by.add(user)

        # Проверяем, все ли подписали
        if self.signers.count() == self.signatures.count():
            self.status = 'signed'
            self.save()

        return signature

    def generate_signature_hash(self, user):
        """Генерирует уникальный хэш подписи"""
        data = {
            'document_id': self.id,
            'user_id': user.id,
            'timestamp': str(timezone.now()),
            'content_hash': self.get_content_hash()
        }
        json_data = json.dumps(data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(json_data).hexdigest()

    def get_content_hash(self):
        """Хэш содержимого документа (можно расширить для файлов)"""
        content = f"{self.title}{self.description}{self.status}"
        for file in self.files.all():
            content += file.name
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def verify_signatures(self):
        """Проверяет все подписи документа"""
        return all(
            self.verify_signature(signature)
            for signature in self.signatures.all()
        )

    def verify_signature(self, signature):
        """Проверяет конкретную подпись"""
        expected_hash = self.generate_signature_hash(signature.user)
        return signature.signature == expected_hash

    def send_to_revision(self):
        """Отправка документа на доработку со сбросом подписей"""
        self.status = 'revision'
        self.signed_by.clear()  # Очищаем стандартные подписи
        self.signatures.all().delete()  # Удаляем все электронные подписи
        self.save()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'


class DocumentSignature(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='signatures')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    signature = models.CharField(max_length=255, unique=True)
    signed_at = models.DateTimeField(auto_now_add=True)
    signature_data = models.JSONField(default=dict)  # Дополнительные данные подписи

    class Meta:
        unique_together = ('document', 'user')
        verbose_name = 'Подпись документа'
        verbose_name_plural = 'Подписи документов'

    def __str__(self):
        return f"Подпись {self.user.username} для документа {self.document.id}"


class DocumentFile(models.Model):
    # Статусы файла
    FILE_STATUS_CHOICES = [
        ('uploaded', 'Загружен'),
        ('deleted', 'Удален'),
    ]

    # Основные поля
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='files', verbose_name='Документ')
    file = models.FileField(upload_to='documents/%Y/%m/%d/', verbose_name='Файл')
    name = models.CharField(max_length=255, verbose_name='Имя файла')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')
    status = models.CharField(max_length=50, choices=FILE_STATUS_CHOICES, default='uploaded', verbose_name='Статус файла')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Файл документа'
        verbose_name_plural = 'Файлы документов'

class DocumentComment(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='comments', verbose_name='Документ')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    message = models.TextField(verbose_name='Сообщение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    is_system = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.created_at}"

    class Meta:
        verbose_name = 'Комментарий к документу'
        verbose_name_plural = 'Комментарии к документам'


class DocumentTemplate(models.Model):
    DOCUMENT_TYPES = [
        ('order', 'Приказ'),
        ('contract', 'Договор'),
        ('act', 'Акт'),
    ]
    name = models.CharField(max_length=255, verbose_name="Название шаблона")
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, verbose_name="Тип документа")
    template_file = models.FileField(upload_to='document_templates/', verbose_name="Файл шаблона")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fields_metadata = models.JSONField(
        verbose_name="Метаданные полей",
        help_text="JSON структура с описанием полей для заполнения",
        default=dict
    )

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.name}"

    class Meta:
        verbose_name = 'Шаблон документа'
        verbose_name_plural = 'Шаблоны документов'
