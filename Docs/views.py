import secrets
from django.contrib.auth import logout
from django.db.models import Q
from django.template.loader import render_to_string
from django.views import View
from .forms import *
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .forms import DocumentForm
from docx import Document as DocxDocument
from django.core.exceptions import ValidationError
from django.urls import reverse
from urllib.parse import unquote
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from django.core.paginator import Paginator
from django.http import JsonResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from .metrics import update_metrics
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.contrib import messages
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.conf import settings
import csv
import os
import zipfile
import subprocess
import io
from django.core.files.storage import FileSystemStorage
from .models import Profile, Document, DocumentSignature, DocumentFile, DocumentComment, DocumentTemplate
from django.contrib.auth.models import User
import json
import logging
from dotenv import load_dotenv


load_dotenv()
# Настройка логирования
logger = logging.getLogger(__name__)


def is_admin(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'admin'

@user_passes_test(is_admin)
def backup_dashboard(request):
    return render(request, 'backup_dashboard.html')

@user_passes_test(is_admin)
def export_csv_backup(request):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f'backup_{timestamp}.zip'
    zip_path = os.path.join(settings.MEDIA_ROOT, zip_filename)

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Экспорт модели Profile
            profile_buffer = io.StringIO()
            profile_buffer.write('\ufeff')  # Добавляем BOM для UTF-8
            profile_writer = csv.writer(profile_buffer)
            profile_writer.writerow(
                ['user_id', 'first_name', 'last_name', 'photo', 'role', 'telegram_id', 'telegram_token'])
            for profile in Profile.objects.all():
                photo_name = profile.photo.name if profile.photo else ''
                profile_writer.writerow([
                    profile.user_id,
                    profile.first_name,
                    profile.last_name,
                    photo_name,
                    profile.role,
                    profile.telegram_id,
                    profile.telegram_token
                ])
            zipf.writestr('profiles.csv', profile_buffer.getvalue().encode('utf-8'))
            profile_buffer.close()

            # Экспорт модели Document
            document_buffer = io.StringIO()
            document_buffer.write('\ufeff')  # Добавляем BOM
            document_writer = csv.writer(document_buffer)
            document_writer.writerow(
                ['id', 'title', 'description', 'status', 'created_at', 'updated_at', 'creators', 'signers',
                 'signed_by'])
            for doc in Document.objects.all():
                document_writer.writerow([
                    doc.id,
                    doc.title,
                    doc.description,
                    doc.status,
                    doc.created_at,
                    doc.updated_at,
                    ','.join(str(user.id) for user in doc.creators.all()),
                    ','.join(str(user.id) for user in doc.signers.all()),
                    ','.join(str(user.id) for user in doc.signed_by.all())
                ])
            zipf.writestr('documents.csv', document_buffer.getvalue().encode('utf-8'))
            document_buffer.close()

            # Экспорт модели DocumentSignature
            signature_buffer = io.StringIO()
            signature_buffer.write('\ufeff')  # Добавляем BOM
            signature_writer = csv.writer(signature_buffer)
            signature_writer.writerow(['document_id', 'user_id', 'signature', 'signed_at', 'signature_data'])
            for sig in DocumentSignature.objects.all():
                signature_writer.writerow([
                    sig.document_id,
                    sig.user_id,
                    sig.signature,
                    sig.signed_at,
                    json.dumps(sig.signature_data)
                ])
            zipf.writestr('document_signatures.csv', signature_buffer.getvalue().encode('utf-8'))
            signature_buffer.close()

            # Экспорт модели DocumentFile
            file_buffer = io.StringIO()
            file_buffer.write('\ufeff')  # Добавляем BOM
            file_writer = csv.writer(file_buffer)
            file_writer.writerow(['document_id', 'file_name', 'name', 'uploaded_at', 'status'])
            for doc_file in DocumentFile.objects.all():
                file_name = doc_file.file.name
                file_writer.writerow([
                    doc_file.document_id,
                    file_name,
                    doc_file.name,
                    doc_file.uploaded_at,
                    doc_file.status
                ])
            zipf.writestr('document_files.csv', file_buffer.getvalue().encode('utf-8'))
            file_buffer.close()

            # Экспорт модели DocumentComment
            comment_buffer = io.StringIO()
            comment_buffer.write('\ufeff')  # Добавляем BOM
            comment_writer = csv.writer(comment_buffer)
            comment_writer.writerow(['document_id', 'user_id', 'message', 'created_at', 'is_system'])
            for comment in DocumentComment.objects.all():
                comment_writer.writerow([
                    comment.document_id,
                    comment.user_id,
                    comment.message,
                    comment.created_at,
                    comment.is_system
                ])
            zipf.writestr('document_comments.csv', comment_buffer.getvalue().encode('utf-8'))
            comment_buffer.close()

            # Экспорт модели DocumentTemplate
            template_buffer = io.StringIO()
            template_buffer.write('\ufeff')  # Добавляем BOM
            template_writer = csv.writer(template_buffer)
            template_writer.writerow(
                ['id', 'name', 'document_type', 'template_file', 'description', 'created_at', 'updated_at',
                 'fields_metadata'])
            for template in DocumentTemplate.objects.all():
                template_file_name = template.template_file.name
                template_writer.writerow([
                    template.id,
                    template.name,
                    template.document_type,
                    template_file_name,
                    template.description,
                    template.created_at,
                    template.updated_at,
                    json.dumps(template.fields_metadata)
                ])
            zipf.writestr('document_templates.csv', template_buffer.getvalue().encode('utf-8'))
            template_buffer.close()

        with open(zip_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename={zip_filename}'
        return response
    except Exception as e:
        logger.error(f"Ошибка экспорта CSV: {str(e)}")
        messages.error(request, f"Ошибка при создании CSV бэкапа: {str(e)}")
        return redirect('backup_dashboard')
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)

@user_passes_test(is_admin)
def export_sql_backup(request):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    sql_filename = f'backup_{timestamp}.sql'
    sql_path = os.path.join(settings.MEDIA_ROOT, sql_filename)

    db_settings = settings.DATABASES['default']
    # Указываем полный путь к pg_dump (замените на актуальный путь)
    pg_dump_path = os.getenv('POSTGRE_DUMP_PATH')  # Настройте путь
    command = [
        pg_dump_path,
        '-h', db_settings['HOST'],
        '-U', db_settings['USER'],
        '-p', db_settings['PORT'],
        '-F', 'p',
        '-f', sql_path,
        db_settings['NAME']
    ]
    env = os.environ.copy()
    env['PGPASSWORD'] = db_settings['PASSWORD']

    try:
        subprocess.run(command, env=env, check=True, capture_output=True, text=True)
        with open(sql_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/sql')
            response['Content-Disposition'] = f'attachment; filename={sql_filename}'
        return response
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка экспорта SQL: {e.stderr or str(e)}")
        messages.error(request, f"Ошибка при создании SQL бэкапа: {e.stderr or str(e)}")
        return redirect('backup_dashboard')
    except Exception as e:
        logger.error(f"Общая ошибка экспорта SQL: {str(e)}")
        messages.error(request, f"Ошибка при создании SQL бэкапа: {str(e)}")
        return redirect('backup_dashboard')
    finally:
        if os.path.exists(sql_path):
            os.remove(sql_path)

@user_passes_test(is_admin)
def import_csv_backup(request):
    if request.method == 'POST' and request.FILES.get('csv_zip'):
        zip_file = request.FILES['csv_zip']
        fs = FileSystemStorage()
        filename = fs.save(zip_file.name, zip_file)
        file_path = fs.path(filename)

        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                # Импорт Profile
                if 'profiles.csv' in zipf.namelist():
                    with zipf.open('profiles.csv') as f:
                        reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
                        for row in reader:
                            try:
                                user = User.objects.get(id=row['user_id'])
                                telegram_id = row['telegram_id'][:100] if row['telegram_id'] else None
                                telegram_token = row['telegram_token'][:100] if row['telegram_token'] else None
                                Profile.objects.update_or_create(
                                    user=user,
                                    defaults={
                                        'first_name': row['first_name'],
                                        'last_name': row['last_name'],
                                        'photo': row['photo'],
                                        'role': row['role'],
                                        'telegram_id': telegram_id,
                                        'telegram_token': telegram_token
                                    }
                                )
                            except Exception as e:
                                logger.error(f"Ошибка импорта профиля user_id={row['user_id']}: {str(e)}")
                                messages.warning(request, f"Ошибка импорта профиля user_id={row['user_id']}: {str(e)}")

                # Импорт Document
                if 'documents.csv' in zipf.namelist():
                    with zipf.open('documents.csv') as f:
                        reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
                        for row in reader:
                            try:
                                doc = Document.objects.update_or_create(
                                    id=row['id'],
                                    defaults={
                                        'title': row['title'],
                                        'description': row['description'],
                                        'status': row['status'],
                                        'created_at': row['created_at'],
                                        'updated_at': row['updated_at']
                                    }
                                )[0]
                                doc.creators.set(User.objects.filter(id__in=row['creators'].split(',')))
                                doc.signers.set(User.objects.filter(id__in=row['signers'].split(',')))
                                doc.signed_by.set(User.objects.filter(id__in=row['signed_by'].split(',')))
                            except Exception as e:
                                logger.error(f"Ошибка импорта документа id={row['id']}: {str(e)}")
                                messages.warning(request, f"Ошибка импорта документа id={row['id']}: {str(e)}")

                # Импорт DocumentSignature
                if 'document_signatures.csv' in zipf.namelist():
                    with zipf.open('document_signatures.csv') as f:
                        reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
                        for row in reader:
                            try:
                                DocumentSignature.objects.update_or_create(
                                    document_id=row['document_id'],
                                    user_id=row['user_id'],
                                    defaults={
                                        'signature': row['signature'],
                                        'signed_at': row['signed_at'],
                                        'signature_data': json.loads(row['signature_data'])
                                    }
                                )
                            except Exception as e:
                                logger.error(
                                    f"Ошибка импорта подписи document_id={row['document_id']}, user_id={row['user_id']}: {str(e)}")
                                messages.warning(request,
                                                f"Ошибка импорта подписи document_id={row['document_id']}: {str(e)}")

                # Импорт DocumentFile
                if 'document_files.csv' in zipf.namelist():
                    with zipf.open('document_files.csv') as f:
                        reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
                        for row in reader:
                            try:
                                DocumentFile.objects.update_or_create(
                                    document_id=row['document_id'],
                                    defaults={
                                        'file': row['file_name'],
                                        'name': row['name'],
                                        'uploaded_at': row['uploaded_at'],
                                        'status': row['status']
                                    }
                                )
                            except Exception as e:
                                logger.error(f"Ошибка импорта файла document_id={row['document_id']}: {str(e)}")
                                messages.warning(request,
                                                f"Ошибка импорта файла document_id={row['document_id']}: {str(e)}")

                # Импорт DocumentComment
                if 'document_comments.csv' in zipf.namelist():
                    with zipf.open('document_comments.csv') as f:
                        reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
                        for row in reader:
                            try:
                                DocumentComment.objects.update_or_create(
                                    document_id=row['document_id'],
                                    user_id=row['user_id'],
                                    created_at=row['created_at'],
                                    defaults={
                                        'message': row['message'],
                                        'is_system': row['is_system'] == 'True'
                                    }
                                )
                            except Exception as e:
                                logger.error(
                                    f"Ошибка импорта комментария document_id={row['document_id']}, user_id={row['user_id']}: {str(e)}")
                                messages.warning(request,
                                                f"Ошибка импорта комментария document_id={row['document_id']}: {str(e)}")

                # Импорт DocumentTemplate
                if 'document_templates.csv' in zipf.namelist():
                    with zipf.open('document_templates.csv') as f:
                        reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
                        for row in reader:
                            try:
                                DocumentTemplate.objects.update_or_create(
                                    id=row['id'],
                                    defaults={
                                        'name': row['name'],
                                        'document_type': row['document_type'],
                                        'template_file': row['template_file'],
                                        'description': row['description'],
                                        'created_at': row['created_at'],
                                        'updated_at': row['updated_at'],
                                        'fields_metadata': json.loads(row['fields_metadata'])
                                    }
                                )
                            except Exception as e:
                                logger.error(f"Ошибка импорта шаблона id={row['id']}: {str(e)}")
                                messages.warning(request, f"Ошибка импорта шаблона id={row['id']}: {str(e)}")

            messages.success(request, 'CSV бэкап успешно импортирован.')
        except Exception as e:
            logger.error(f"Общая ошибка импорта CSV: {str(e)}")
            messages.error(request, f"Ошибка при импорте CSV: {str(e)}")
        finally:
            if os.path.exists(file_path):
                fs.delete(filename)

        return redirect('backup_dashboard')
    return redirect('backup_dashboard')


from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings
import subprocess
import os
import logging

logger = logging.getLogger(__name__)

@user_passes_test(is_admin)
def import_sql_backup(request):
    if request.method == 'POST' and request.FILES.get('sql_file'):
        sql_file = request.FILES['sql_file']
        if not sql_file.name.endswith('.sql'):
            messages.error(request, "Ошибка: файл должен быть в формате .sql")
            return redirect('backup_dashboard')

        fs = FileSystemStorage()
        filename = fs.save(sql_file.name, sql_file)
        file_path = fs.path(filename)

        db_settings = settings.DATABASES['default']
        psql_path = os.getenv('POSTGRE_PSQL_PATH')

        if not psql_path or not os.path.exists(psql_path):
            logger.error(f"Не найден psql.exe по пути: {psql_path}")
            messages.error(request, "Ошибка: не найден psql.exe. Проверьте POSTGRE_PSQL_PATH.")
            fs.delete(filename)
            return redirect('backup_dashboard')

        # Проверка наличия psycopg2
        try:
            import psycopg2
        except ImportError:
            logger.error("Модуль psycopg2 не установлен")
            messages.error(request, "Ошибка: модуль psycopg2 не установлен. Установите его с помощью 'pip install psycopg2-binary'.")
            fs.delete(filename)
            return redirect('backup_dashboard')

        # Очистка таблицы перед импортом
        try:
            logger.info(f"Настройки базы данных: {db_settings}")
            conn = psycopg2.connect(
                dbname=db_settings['NAME'],
                user=db_settings['USER'],
                password=db_settings['PASSWORD'],
                host=db_settings['HOST'],
                port=db_settings.get('PORT', '5432')
            )
            cursor = conn.cursor()
            cursor.execute('TRUNCATE TABLE public."Docs_document" RESTART IDENTITY CASCADE;')
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("Таблица Docs_document и связанные таблицы успешно очищены")
        except Exception as e:
            logger.error(f"Ошибка очистки таблицы: {str(e)}")
            messages.error(request, f"Ошибка при очистке таблицы: {str(e)}")
            fs.delete(filename)
            return redirect('backup_dashboard')

        # Логирование содержимого файла
        try:
            with open(file_path, 'r') as f:
                file_preview = f.read(1000)
                logger.info(f"Содержимое SQL-файла: {file_preview}")
        except Exception as e:
            logger.warning(f"Не удалось прочитать содержимое файла: {str(e)}")

        command = [
            psql_path,
            '-h', db_settings['HOST'],
            '-U', db_settings['USER'],
            '-d', db_settings['NAME'],
            '-p', str(db_settings.get('PORT', '5432')),
            '-f', file_path
        ]
        env = os.environ.copy()
        env['PGPASSWORD'] = db_settings['PASSWORD']

        try:
            result = subprocess.run(command, env=env, check=True, capture_output=True, text=True)
            logger.info(f"Команда выполнена успешно. Вывод: {result.stdout}")
            messages.success(request, 'SQL бэкап успешно импортирован.')
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка импорта SQL: {e.stderr or str(e)}")
            messages.error(request, f"Ошибка при импорте SQL бэкапа: {e.stderr or str(e)}")
        finally:
            fs.delete(filename)

        return redirect('backup_dashboard')
    return redirect('backup_dashboard')

@user_passes_test(is_admin)
def delete_document(request, pk):
    """Удаляет документ, если пользователь — администратор."""
    if request.user.profile.role != 'admin':
        messages.error(request, "У вас нет прав для удаления документов.")
        return redirect('document_list')

    document = get_object_or_404(Document, pk=pk)

    if request.method == 'POST':
        document_title = document.title
        document.delete()
        messages.success(request, f"Документ '{document_title}' успешно удалён.")
        return redirect('document_list')

    # Если метод не POST, перенаправляем на список документов
    return redirect('document_list')


@user_passes_test(is_admin)
def admin_panel(request):
    users = User.objects.select_related('profile').order_by('last_name', 'first_name')
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_panel.html', {
        'users': page_obj,
    })


@user_passes_test(is_admin)
def admin_change_role(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_role = request.POST.get('new_role')

        try:
            user = User.objects.get(pk=user_id)
            user.profile.role = new_role
            user.profile.save()
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Пользователь не найден'})

    return JsonResponse({'success': False, 'error': 'Неверный запрос'})

def prometheus_metrics(request):
    """Экспортирует пользовательские метрики и метрики django-prometheus."""
    update_metrics()  # Обновляем пользовательские метрики
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)


class CustomLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')


def login_disabled_view(request):
    return render(request, 'login_disabled.html')


def home(request):
    return render(request, 'index.html')


# Функция для проверки роли "Секретарь"
def is_secretary(user):
    return user.profile.role == 'secretary'

@login_required
def export_documents_pdf(request):
    # Проверка роли
    if not is_secretary(request.user):
        return HttpResponse('У вас нет прав для доступа к этому ресурсу.', status=403)

    # Ответ с PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="documents.pdf"'

    # Создаем буфер
    doc = SimpleDocTemplate(response, pagesize=A4)

    # Регистрируем шрифт Times New Roman
    pdfmetrics.registerFont(TTFont('TimesNewRoman', 'C:/Windows/Fonts/times.ttf'))

    # Получаем все документы
    documents = Document.objects.all().order_by('-created_at')

    # Данные для таблицы
    data = [['ID', 'Название', 'Статус', 'Создан']]

    # Заполняем таблицу данными
    for doc_item in documents:
        data.append([
            str(doc_item.id),
            doc_item.title,  # Используем поле title
            doc_item.status,  # Используем поле status
            doc_item.created_at.strftime('%d.%m.%Y')
        ])

    # Стиль для таблицы и текста
    style = getSampleStyleSheet()
    style['Normal'].fontName = 'TimesNewRoman'
    style['Normal'].fontSize = 12

    # Создаем таблицу
    table = Table(data, colWidths=[40, 150, 80, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'TimesNewRoman'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Добавляем таблицу в документ
    elements = [table]
    doc.build(elements)

    return response


@login_required
def bind_telegram(request):
    # Генерируем токен
    token = secrets.token_urlsafe(16)

    profile = request.user.profile
    profile.telegram_token = token
    profile.save()

    bot_username = "Shool654Bot"
    deep_link = f"https://t.me/{bot_username}?start={token}"

    return render(request, 'bind_telegram.html', {
        'deep_link': deep_link
    })


@login_required
def select_document_type(request):
    # Показываем страницу с выбором типа документа
    return render(request, 'templated_document/select_document_type.html')

@login_required
def create_templated_document(request, document_type):
    if document_type == 'act':
        form_class = ActDocumentForm
    elif document_type == 'contract':
        form_class = ContractDocumentForm
    elif document_type == 'order':
        form_class = OrderDocumentForm
    else:
        return HttpResponse('Тип документа не найден', status=400)

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            # Определение шаблона и имени файла
            if document_type == 'act':
                template_path = os.path.join(settings.BASE_DIR, 'templates', 'act_template.docx')
                identifier = data['act_number']
            elif document_type == 'contract':
                template_path = os.path.join(settings.BASE_DIR, 'templates', 'contract_template.docx')
                identifier = data['contract_number']
            elif document_type == 'order':
                template_path = os.path.join(settings.BASE_DIR, 'templates', 'order_template.docx')
                identifier = data['document_number']

            # Открытие шаблона
            doc = DocxDocument(template_path)

            # Замена плейсхолдеров
            for para in doc.paragraphs:
                text = para.text

                if document_type == 'act':
                    members = [m.strip() for m in data.get('commission_members', '').split(',')]
                    members_list = "\n".join(f"- {m}" for m in members)
                    member_signatures = "\n".join(f"__________________ / {m} /" for m in members)

                    replacements = {
                        '{{ act_number }}': data['act_number'],
                        '{{ city }}': data['city'],
                        '{{ date }}': str(data['date']),
                        '{{ title }}': data['title'],
                        '{{ customer }}': data['customer'],
                        '{{ executor }}': data['executor'],
                        '{{ work_description }}': data['work_description'],
                        '{{ work_result }}': data['work_result'],
                        '{{ commission_members_list }}': members_list,
                        '{{ commission_signatures }}': member_signatures,
                    }

                elif document_type == 'contract':
                    replacements = {
                        '{{ contract_number }}': data['contract_number'],
                        '{{ city }}': data['city'],
                        '{{ contract_date }}': str(data['contract_date']),
                        '{{ executor_name }}': data['executor_name'],
                        '{{ signature_executor }}': data['signature_executor'],
                        '{{ customer_name }}': data['customer_name'],
                        '{{ signature_customer }}': data['signature_customer'],
                        '{{ subject }}': data['subject'],
                        '{{ price }}': str(data['price']),
                        '{{ payment_terms }}': data['payment_terms'],
                        '{{ contract_term }}': str(data['contract_term']),
                        '{{ executor_details }}': data['executor_details'],
                        '{{ customer_details }}': data['customer_details'],
                    }

                elif document_type == 'order':
                    items = [i.strip() for i in data.get('items', '').split(',')]
                    items_list = "\n".join(f"{index + 1}. {item}" for index, item in enumerate(items))

                    replacements = {
                        '{{ document_number }}': data['document_number'],
                        '{{ city }}': data['city'],
                        '{{ date }}': str(data['date']),
                        '{{ title }}': data['title'],
                        '{{ basis }}': data['basis'],
                        '{{ items_list }}': items_list,
                        '{{ responsible_person }}': data['responsible_person'],
                        '{{ director_name }}': data['director_name'],
                    }

                for key, value in replacements.items():
                    text = text.replace(key, value)
                para.text = text

            # Сохраняем файл
            today = datetime.today()
            year = today.year
            month = today.month
            day = today.day
            filename = f"{identifier}_{today.strftime('%Y-%m-%d')}.docx"
            save_dir = os.path.join(settings.MEDIA_ROOT, 'documents', str(year), str(month), str(day))
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, filename)
            doc.save(save_path)

            file_url = f"/media/documents/{year}/{month}/{day}/{filename}"
            return redirect(f"{reverse('document_created')}?file_url={file_url}")

    else:
        form = form_class()

    return render(request, 'templated_document/create_templated_document.html', {'form': form})


@login_required
def document_created(request):
    file_url = request.GET.get('file_url')
    if file_url:
        file_url = unquote(file_url)
    return render(request, 'templated_document/document_created.html', {'file_url': file_url})


@login_required
def create_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, current_user=request.user)
        files = request.FILES.getlist('files')

        if form.is_valid():
            document = form.save(commit=False)
            document.save()

            # Получаем списки из формы
            creators = list(form.cleaned_data['creators'])
            signers = list(form.cleaned_data['signers'])

            # Добавляем текущего пользователя, если его нет
            if request.user not in creators:
                creators.append(request.user)

            # Добавляем всех инициаторов в подписанты
            for creator in creators:
                if creator not in signers:
                    signers.append(creator)

            # Сохраняем
            document.creators.set(creators)
            document.signers.set(signers)

            # Загрузка файлов
            for file in files:
                DocumentFile.objects.create(
                    document=document,
                    file=file,
                    name=file.name
                )

            return redirect('document_detail', pk=document.pk)
    else:
        form = DocumentForm(current_user=request.user)

    return render(request, 'documents/document_form.html', {'form': form})


@login_required
def edit_document(request, pk):
    document = get_object_or_404(Document, pk=pk)

    if request.user not in document.creators.all():
        messages.error(request, "Вы не являетесь инициатором этого документа.")
        return redirect('document_detail', pk=pk)

    # Проверка, что документ в статусе "На доработке"
    if document.status != 'revision' and request.method == 'GET':
        messages.error(request, "Документ можно редактировать только в статусе 'На доработке'.")
        return redirect('document_detail', pk=pk)

    if request.method == 'POST':
        form = DocumentForm(request.POST, instance=document, current_user=request.user)
        files = request.FILES.getlist('files')

        # Обработка завершения доработки
        if 'finish_revision' in request.POST:
            document.status = 'pending'
            document.save()

            # Системный комментарий
            DocumentComment.objects.create(
                document=document,
                user=request.user,
                message="Документ завершил доработку и готов к подписанию",
                is_system=True
            )

            messages.success(request, "Документ готов к подписанию.")
            return redirect('document_detail', pk=document.pk)

        # Обработка отправки на доработку
        if 'send_to_revision' in request.POST:
            document.send_to_revision()

            # Системный комментарий
            DocumentComment.objects.create(
                document=document,
                user=request.user,
                message="Документ отправлен на доработку, все подписи сброшены",
                is_system=True
            )

            messages.info(request, "Документ отправлен на доработку, подписи сброшены.")
            return redirect('document_detail', pk=document.pk)

        if form.is_valid():
            document = form.save(commit=False)
            document.save()

            # Обновление инициаторов и подписантов
            creators = list(form.cleaned_data['creators'])
            signers = list(form.cleaned_data['signers'])

            if request.user not in creators:
                creators.append(request.user)

            for creator in creators:
                if creator not in signers:
                    signers.append(creator)

            document.creators.set(creators)
            document.signers.set(signers)

            # Сохранение новых файлов
            for file in files:
                DocumentFile.objects.create(
                    document=document,
                    file=file,
                    name=file.name
                )

            messages.success(request, "Документ успешно обновлён.")
            return redirect('document_detail', pk=document.pk)
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = DocumentForm(instance=document, current_user=request.user)
        comment_form = DocumentCommentForm()

    files = document.files.filter(status='uploaded')
    is_creator = request.user in document.creators.all()

    return render(request, 'documents/document_edit.html', {
        'form': form,
        'files': files,
        'document': document,
        'comment_form': comment_form,
        'is_creator': is_creator,
    })


@login_required
def document_detail(request, pk):
    """Возвращает страницу детальной информации о документе"""
    document = get_object_or_404(Document, pk=pk)
    user = request.user

    is_signer = user in document.signers.all()
    has_signed = user in document.signed_by.all()

    # Обработка добавления комментария
    comment_form = DocumentCommentForm(request.POST or None)

    is_director = hasattr(user, 'profile') and user.profile.role == 'director'
    all_signed = document.signers.count() == document.signed_by.count()

    # Проверка прав подписи
    can_sign = (
        user in document.signers.all() and
        not document.signatures.filter(user=user).exists()
    )

    if request.method == 'POST':
        # Подписание документа
        if 'sign' in request.POST and can_sign:
            try:
                signature_data = {
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                }

                # Добавляем подпись
                signature = document.add_signature(user, signature_data)

                # Системный комментарий
                DocumentComment.objects.create(
                    document=document,
                    user=user,
                    message=f"Документ подписан электронной подписью пользователем {user.get_full_name()}",
                    is_system=True
                )

                messages.success(request, "Документ успешно подписан")
                return redirect('document_detail', pk=pk)

            except ValidationError as e:
                messages.error(request, str(e))

        # Принятие документа директором
        elif 'accept' in request.POST and is_director and document.status == 'signed':
            document.status = 'accept'
            document.save()
            # Добавляем системное сообщение о принятии
            DocumentComment.objects.create(
                document=document,
                user=user,
                message=f"Документ принят директором {user.get_full_name()}",
                is_system=True
            )
            messages.success(request, "Документ принят директором.")

        # Обновляем статус, если все подписали, но не директор ещё
        if document.status != 'accept' and document.signers.count() == document.signed_by.count():
            document.status = 'signed'
            document.save()
            # Добавляем системное сообщение о статусе
            DocumentComment.objects.create(
                document=document,
                user=user,
                message="Все подписанты подписали документ. Статус обновлён на 'Подписан'.",
                is_system=True
            )

        # Обработка отправки комментария
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.document = document
            comment.user = user
            comment.save()
            messages.success(request, "Комментарий успешно добавлен.")
            return redirect('document_detail', pk=pk)

    signatures = document.signatures.select_related('user').all()

    return render(request, 'documents/document_detail.html', {
        'signatures': signatures,
        'document': document,
        'is_signer': is_signer,
        'has_signed': has_signed,
        'can_sign': can_sign,
        'is_director': is_director,
        'all_signed': all_signed,
        'comment_form': comment_form,
    })

def document_comments(request, pk):
    document = get_object_or_404(Document, pk=pk)
    comments = document.comments.all().order_by('-created_at')

    paginator = Paginator(comments, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    comments_html = render_to_string('documents/_comments_partial.html', {
        'comments': page_obj,
    }, request=request)

    return JsonResponse({
        'comments_html': comments_html,
        'total_pages': paginator.num_pages,
    })

@login_required
def delete_file(request, file_id):
    file = get_object_or_404(DocumentFile, id=file_id)
    file.status = 'deleted'
    file.save()
    return redirect('edit_document', pk=file.document.pk)


def document_list(request):
    status_filter = request.GET.get('status', '')
    academic_year_filter = request.GET.get('academic_year', '')
    creator_filter = request.GET.get('creator', '')
    signer_filter = request.GET.get('signer', '')
    search_query = request.GET.get('search', '')
    is_partial = request.GET.get('partial', False)

    documents = Document.objects.all().order_by('-created_at')

    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if status_filter and status_filter != 'all':
        documents = documents.filter(status=status_filter)

    if academic_year_filter:
        start_year, end_year = map(int, academic_year_filter.split('-'))
        documents = documents.filter(created_at__year__gte=start_year, created_at__year__lte=end_year)

    if creator_filter:
        documents = documents.filter(creators__id=creator_filter)

    if signer_filter:
        documents = documents.filter(signers__id=signer_filter)

    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    years = [(year, year + 1) for year in range(2020, 2025)]
    creators = User.objects.filter(created_documents__isnull=False).distinct()
    signers = User.objects.filter(documents_to_sign__isnull=False).distinct()

    context = {
        'documents': page_obj,
        'years': years,
        'creators': creators,
        'signers': signers,
        'status_filter': status_filter,
        'academic_year_filter': academic_year_filter,
        'creator_filter': creator_filter,
        'signer_filter': signer_filter,
        'search_query': search_query,
    }

    if is_partial:
        html = render_to_string('documents/_documents_table_partial.html', context, request=request)
        return JsonResponse({'html': html})

    return render(request, 'documents/document_list.html', context)

@login_required
def profile_view(request):
    user = request.user
    profile = user.profile
    documents_to_sign = Document.objects.filter(
        signers=user,
    ).exclude(signed_by=user)

    context = {
        'user': user,
        'profile': profile,
        'documents': documents_to_sign,  # Именно эта переменная используется в шаблоне
    }

    return render(request, 'profile.html', context)


@login_required
def profile_edit(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = ProfilePhotoForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')  # или куда нужно
    else:
        form = ProfilePhotoForm(instance=profile)

    return render(request, 'edit_photo.html', {'form': form})


@login_required
def unbind_telegram(request):
    """Отвязываем Telegram аккаунт от профиля пользователя."""
    profile = request.user.profile

    if profile.telegram_id:
        profile.telegram_id = None  # Убираем Telegram ID
        profile.save()
        messages.success(request, "Ваш Telegram аккаунт успешно отвязан.")
    else:
        messages.warning(request, "Ваш Telegram аккаунт не был привязан.")

    return redirect('profile')