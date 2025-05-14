from django import forms
from .models import Document, DocumentFile, Profile, DocumentComment
from django.contrib.auth.models import User
from django.utils import timezone
import os

# -------------------- ActDocumentForm --------------------
class ActDocumentForm(forms.Form):
    act_number = forms.CharField(label='Номер акта', max_length=100, min_length=1)
    city = forms.CharField(label='Город', max_length=100, min_length=2)
    date = forms.DateField(label='Дата', input_formats=['%d.%m.%Y'],
                           widget=forms.TextInput(attrs={'class': 'flatpickr', 'placeholder': 'дд.мм.гггг'}))
    title = forms.CharField(label='Заголовок', max_length=200, min_length=5)
    customer = forms.CharField(label='Заказчик', max_length=100, min_length=2)
    executor = forms.CharField(label='Исполнитель', max_length=100, min_length=2)
    work_description = forms.CharField(label='Описание работы', widget=forms.Textarea, min_length=10)
    work_result = forms.CharField(label='Результат работы', widget=forms.Textarea, min_length=10)
    commission_members = forms.CharField(label='Члены комиссии', widget=forms.Textarea, min_length=5)

    def clean_act_number(self):
        value = self.cleaned_data['act_number']
        if not value.replace('-', '').replace('/', '').isalnum():
            raise forms.ValidationError('Номер акта должен содержать только буквы, цифры, дефисы или слэши.')
        return value

    def clean_city(self):
        value = self.cleaned_data['city']
        if not all(c.isalpha() or c.isspace() or c == '-' for c in value):
            raise forms.ValidationError('Город должен содержать только буквы, пробелы или дефисы.')
        return value

    def clean_date(self):
        value = self.cleaned_data['date']
        if value > timezone.now().date():
            raise forms.ValidationError('Дата не может быть в будущем.')
        return value

    def clean_commission_members(self):
        value = self.cleaned_data['commission_members']
        members = [m.strip() for m in value.split(',') if m.strip()]
        if len(members) < 2:
            raise forms.ValidationError('Укажите как минимум двух членов комиссии.')
        return value

# -------------------- OrderDocumentForm --------------------
class OrderDocumentForm(forms.Form):
    document_number = forms.CharField(label='Номер приказа', max_length=100, min_length=1)
    city = forms.CharField(label='Город', max_length=100, min_length=2)
    date = forms.DateField(label='Дата приказа', input_formats=['%d.%m.%Y'],
                           widget=forms.TextInput(attrs={'class': 'flatpickr', 'placeholder': 'дд.мм.гггг'}))
    title = forms.CharField(label='Заголовок', max_length=200, min_length=5)
    basis = forms.CharField(label='На основании', widget=forms.Textarea, min_length=10)
    items = forms.CharField(label='Пункты приказа', widget=forms.Textarea, min_length=10)
    responsible_person = forms.CharField(label='Ответственный', max_length=100, min_length=2)
    director_name = forms.CharField(label='Имя директора', max_length=100, min_length=2)

    def clean_document_number(self):
        value = self.cleaned_data['document_number']
        if not value.replace('-', '').replace('/', '').isalnum():
            raise forms.ValidationError('Номер приказа должен содержать только буквы, цифры, дефисы или слэши.')
        return value

    def clean_city(self):
        value = self.cleaned_data['city']
        if not all(c.isalpha() or c.isspace() or c == '-' for c in value):
            raise forms.ValidationError('Город должен содержать только буквы, пробелы или дефисы.')
        return value

    def clean_date(self):
        value = self.cleaned_data['date']
        if value > timezone.now().date():
            raise forms.ValidationError('Дата не может быть в будущем.')
        return value

    def clean_items(self):
        value = self.cleaned_data['items']
        items = [i.strip() for i in value.split(',') if i.strip()]
        if len(items) < 1:
            raise forms.ValidationError('Укажите как минимум один пункт.')
        return value

# -------------------- ContractDocumentForm --------------------
class ContractDocumentForm(forms.Form):
    city = forms.CharField(label='Город', max_length=100, min_length=2)
    contract_date = forms.DateField(label='Дата договора', input_formats=['%d.%m.%Y'],
                                    widget=forms.TextInput(attrs={'class': 'flatpickr', 'placeholder': 'дд.мм.гггг'}))
    contract_term = forms.DateField(label='Срок действия', input_formats=['%d.%m.%Y'],
                                    widget=forms.TextInput(attrs={'class': 'flatpickr', 'placeholder': 'дд.мм.гггг'}))
    contract_number = forms.CharField(label='Номер договора', max_length=100, min_length=1)
    executor_name = forms.CharField(label='Исполнитель', max_length=100, min_length=2)
    signature_executor = forms.CharField(label='Подпись исполнителя', max_length=100, min_length=2)
    customer_name = forms.CharField(label='Заказчик', max_length=100, min_length=2)
    signature_customer = forms.CharField(label='Подпись заказчика', max_length=100, min_length=2)
    subject = forms.CharField(label='Предмет договора', widget=forms.Textarea, min_length=10)
    price = forms.DecimalField(label='Стоимость', max_digits=10, decimal_places=2, min_value=0.01)
    payment_terms = forms.CharField(label='Условия оплаты', widget=forms.Textarea, min_length=10)
    executor_details = forms.CharField(label='Реквизиты исполнителя', widget=forms.Textarea, min_length=10)
    customer_details = forms.CharField(label='Реквизиты заказчика', widget=forms.Textarea, min_length=10)

    def clean_city(self):
        value = self.cleaned_data['city']
        if not all(c.isalpha() or c.isspace() or c == '-' for c in value):
            raise forms.ValidationError('Город должен содержать только буквы, пробелы или дефисы.')
        return value

    def clean_contract_term(self):
        contract_term = self.cleaned_data['contract_term']
        contract_date = self.cleaned_data.get('contract_date')
        if contract_date and contract_term <= contract_date:
            raise forms.ValidationError('Срок действия должен быть позже даты договора.')
        return contract_term

    def clean_contract_number(self):
        value = self.cleaned_data['contract_number']
        if not value.replace('-', '').replace('/', '').isalnum():
            raise forms.ValidationError('Номер договора должен содержать только буквы, цифры, дефисы или слэши.')
        return value

# -------------------- DocumentForm --------------------
class DocumentForm(forms.ModelForm):
    creators = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Инициаторы'
    )
    signers = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Дополнительные подписанты'
    )

    class Meta:
        model = Document
        fields = ['title', 'description', 'creators', 'signers']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        if self.current_user:
            self.fields['creators'].queryset = User.objects.exclude(id=self.current_user.id)
            self.fields['signers'].queryset = User.objects.exclude(id=self.current_user.id)

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if len(title) < 5:
            raise forms.ValidationError('Название должно быть не короче 5 символов.')
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if description and len(description) < 10:
            raise forms.ValidationError('Описание должно быть минимум 10 символов.')
        return description

class DocumentFileForm(forms.ModelForm):
    class Meta:
        model = DocumentFile
        fields = ['file', 'name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input mt-1 block w-full rounded-lg border-gray-300'
            })
        }
        error_messages = {
            'file': {
                'required': 'Файл обязателен.'
            },
            'name': {
                'required': 'Имя файла обязательно.',
                'max_length': 'Имя файла не должно превышать 255 символов.'
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].required = True
        self.fields['name'].required = True

    def clean_file(self):
        file = self.cleaned_data['file']
        max_size = 10 * 1024 * 1024  # 10 MB
        if file.size > max_size:
            raise forms.ValidationError('Размер файла не должен превышать 10 МБ.')
        allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.png']
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in allowed_extensions:
            raise forms.ValidationError('Недопустимый формат файла. Разрешены: PDF, DOC, DOCX, JPG, PNG.')
        return file

    def clean_name(self):
        name = self.cleaned_data['name']
        if len(name.strip()) < 3:
            raise forms.ValidationError('Имя файла должно содержать минимум 3 символа.')
        if not name.replace('.', '').replace('_', '').replace('-', '').isalnum():
            raise forms.ValidationError('Имя файла должно содержать только буквы, цифры, точки, дефисы или подчеркивания.')
        return name

class ProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['photo']
        widgets = {
            'photo': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            })
        }
        error_messages = {
            'photo': {
                'required': 'Фото профиля обязательно.'
            }
        }

    def clean_photo(self):
        photo = self.cleaned_data['photo']
        max_size = 5 * 1024 * 1024  # 5 MB
        if photo.size > max_size:
            raise forms.ValidationError('Размер фото не должен превышать 5 МБ.')
        allowed_extensions = ['.jpg', '.jpeg', '.png']
        ext = os.path.splitext(photo.name)[1].lower()
        if ext not in allowed_extensions:
            raise forms.ValidationError('Недопустимый формат фото. Разрешены: JPG, JPEG, PNG.')
        return photo

class DocumentCommentForm(forms.ModelForm):
    class Meta:
        model = DocumentComment
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'border p-2 rounded w-full',
                'placeholder': 'Напишите комментарий...'
            })
        }
        error_messages = {
            'message': {
                'required': 'Комментарий обязателен.'
            }
        }

    def clean_message(self):
        message = self.cleaned_data['message']
        if len(message.strip()) < 5:
            raise forms.ValidationError('Комментарий должен содержать минимум 5 символов.')
        if len(message) > 1000:
            raise forms.ValidationError('Комментарий не должен превышать 1000 символов.')
        return message