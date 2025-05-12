from django import forms
from .models import Document, DocumentFile, Profile, DocumentComment
from django.contrib.auth.models import User
from datetime import timezone
import os

class ActDocumentForm(forms.Form):
    act_number = forms.CharField(
        label='Номер акта',
        max_length=100,
        min_length=1,
        strip=True,
        error_messages={
            'required': 'Номер акта обязателен.',
            'max_length': 'Номер акта не должен превышать 100 символов.',
            'min_length': 'Номер акта не может быть пустым.',
        }
    )
    city = forms.CharField(
        label='Город',
        max_length=100,
        min_length=2,
        strip=True,
        error_messages={
            'required': 'Город обязателен.',
            'max_length': 'Название города не должно превышать 100 символов.',
            'min_length': 'Название города должно содержать минимум 2 символа.',
        }
    )
    date = forms.DateField(
        label='Дата',
        input_formats=['%d.%m.%Y'],
        widget=forms.TextInput(attrs={'class': 'flatpickr', 'placeholder': 'дд.мм.гггг'}),
        error_messages={
            'required': 'Дата обязательна.',
            'invalid': 'Введите дату в формате дд.мм.гггг.',
        }
    )
    title = forms.CharField(
        label='Заголовок',
        max_length=200,
        min_length=5,
        strip=True,
        error_messages={
            'required': 'Заголовок обязателен.',
            'max_length': 'Заголовок не должен превышать 200 символов.',
            'min_length': 'Заголовок должен содержать минимум 5 символов.',
        }
    )
    customer = forms.CharField(
        label='Заказчик',
        max_length=100,
        min_length=2,
        strip=True,
        error_messages={
            'required': 'Заказчик обязателен.',
            'max_length': 'Имя заказчика не должно превышать 100 символов.',
            'min_length': 'Имя заказчика должно содержать минимум 2 символа.',
        }
    )
    executor = forms.CharField(
        label='Исполнитель',
        max_length=100,
        min_length=2,
        strip=True,
        error_messages={
            'required': 'Исполнитель обязателен.',
            'max_length': 'Имя исполнителя не должно превышать 100 символов.',
            'min_length': 'Имя исполнителя должно содержать минимум 2 символа.',
        }
    )
    work_description = forms.CharField(
        label='Описание работы',
        widget=forms.Textarea,
        min_length=10,
        strip=True,
        error_messages={
            'required': 'Описание работы обязательно.',
            'min_length': 'Описание работы должно содержать минимум 10 символов.',
        }
    )
    work_result = forms.CharField(
        label='Результат работы',
        widget=forms.Textarea,
        min_length=10,
        strip=True,
        error_messages={
            'required': 'Результат работы обязателен.',
            'min_length': 'Результат работы должен содержать минимум 10 символов.',
        }
    )
    commission_members = forms.CharField(
        label='Члены комиссии',
        widget=forms.Textarea,
        help_text="Список членов комиссии, разделенных запятыми.",
        min_length=5,
        strip=True,
        error_messages={
            'required': 'Члены комиссии обязательны.',
            'min_length': 'Список членов комиссии должен содержать минимум 5 символов.',
        }
    )

    def clean_act_number(self):
        act_number = self.cleaned_data['act_number']
        if not act_number.replace('-', '').replace('/', '').isalnum():
            raise forms.ValidationError('Номер акта должен содержать только буквы, цифры, дефисы или слэши.')
        return act_number

    def clean_city(self):
        city = self.cleaned_data['city']
        if not all(c.isalpha() or c.isspace() or c == '-' for c in city):
            raise forms.ValidationError('Город должен содержать только буквы, пробелы или дефисы.')
        return city

    def clean_date(self):
        date = self.cleaned_data['date']
        if date > timezone.now().date():
            raise forms.ValidationError('Дата не может быть в будущем.')
        return date

    def clean_commission_members(self):
        members = self.cleaned_data['commission_members']
        member_list = [m.strip() for m in members.split(',') if m.strip()]
        if len(member_list) < 2:
            raise forms.ValidationError('Укажите как минимум двух членов комиссии.')
        return members

class OrderDocumentForm(forms.Form):
    document_number = forms.CharField(
        label='Номер приказа',
        max_length=100,
        min_length=1,
        strip=True,
        error_messages={
            'required': 'Номер приказа обязателен.',
            'max_length': 'Номер приказа не должен превышать 100 символов.',
            'min_length': 'Номер приказа не может быть пустым.',
        }
    )
    city = forms.CharField(
        label='Город',
        max_length=100,
        min_length=2,
        strip=True,
        error_messages={
            'required': 'Город обязателен.',
            'max_length': 'Название города не должно превышать 100 символов.',
            'min_length': 'Название города должно содержать минимум 2 символа.',
        }
    )
    date = forms.DateField(
        label='Дата приказа',
        input_formats=['%d.%m.%Y'],
        widget=forms.TextInput(attrs={'class': 'flatpickr', 'placeholder': 'дд.мм.гггг'}),
        error_messages={
            'required': 'Дата приказа обязательна.',
            'invalid': 'Введите дату в формате дд.мм.гггг.',
        }
    )
    title = forms.CharField(
        label='Заголовок',
        max_length=200,
        min_length=5,
        strip=True,
        error_messages={
            'required': 'Заголовок обязателен.',
            'max_length': 'Заголовок не должен превышать 200 символов.',
            'min_length': 'Заголовок должен содержать минимум 5 символов.',
        }
    )
    basis = forms.CharField(
        label='На основании',
        widget=forms.Textarea,
        min_length=10,
        strip=True,
        error_messages={
            'required': 'Поле "На основании" обязательно.',
            'min_length': 'Поле "На основании" должно содержать минимум 10 символов.',
        }
    )
    items = forms.CharField(
        label='Пункты приказа',
        widget=forms.Textarea,
        help_text="Список пунктов приказа, разделенных запятыми.",
        min_length=10,
        strip=True,
        error_messages={
            'required': 'Пункты приказа обязательны.',
            'min_length': 'Пункты приказа должны содержать минимум 10 символов.',
        }
    )
    responsible_person = forms.CharField(
        label='Ответственный за исполнение',
        max_length=100,
        min_length=2,
        strip=True,
        error_messages={
            'required': 'Ответственный за исполнение обязателен.',
            'max_length': 'Имя ответственного не должно превышать 100 символов.',
            'min_length': 'Имя ответственного должно содержать минимум 2 символа.',
        }
    )
    director_name = forms.CharField(
        label='Имя директора',
        max_length=100,
        min_length=2,
        strip=True,
        error_messages={
            'required': 'Имя директора обязательно.',
            'max_length': 'Имя директора не должно превышать 100 символов.',
            'min_length': 'Имя директора должно содержать минимум 2 символа.',
        }
    )

    def clean_document_number(self):
        document_number = self.cleaned_data['document_number']
        if not document_number.replace('-', '').replace('/', '').isalnum():
            raise forms.ValidationError('Номер приказа должен содержать только буквы, цифры, дефисы или слэши.')
        return document_number

    def clean_city(self):
        city = self.cleaned_data['city']
        if not all(c.isalpha() or c.isspace() or c == '-' for c in city):
            raise forms.ValidationError('Город должен содержать только буквы, пробелы или дефисы.')
        return city

    def clean_date(self):
        date = self.cleaned_data['date']
        if date > timezone.now().date():
            raise forms.ValidationError('Дата приказа не может быть в будущем.')
        return date

    def clean_items(self):
        items = self.cleaned_data['items']
        item_list = [i.strip() for i in items.split(',') if i.strip()]
        if len(item_list) < 1:
            raise forms.ValidationError('Укажите как минимум один пункт приказа.')
        return items

    def clean_responsible_person(self):
        responsible_person = self.cleaned_data['responsible_person']
        if not all(c.isalpha() or c.isspace() or c == '-' for c in responsible_person):
            raise forms.ValidationError('Имя ответственного должно содержать только буквы, пробелы или дефисы.')
        return responsible_person

    def clean_director_name(self):
        director_name = self.cleaned_data['director_name']
        if not all(c.isalpha() or c.isspace() or c == '-' for c in director_name):
            raise forms.ValidationError('Имя директора должно содержать только буквы, пробелы или дефисы.')
        return director_name


class ContractDocumentForm(forms.Form):
    city = forms.CharField(
        label='Город',
        max_length=100,
        min_length=2,
        strip=True,
        error_messages={
            'required': 'Город обязателен.',
            'max_length': 'Название города не должно превышать 100 символов.',
            'min_length': 'Название города должно содержать минимум 2 символа.',
        }
    )
    contract_date = forms.DateField(
        label='Дата договора',
        input_formats=['%d.%m.%Y'],
        widget=forms.TextInput(attrs={'class': 'flatpickr', 'placeholder': 'дд.мм.гггг'}),
        error_messages={
            'required': 'Дата договора обязательна.',
            'invalid': 'Введите дату в формате дд.мм.гггг.',
        }
    )
    executor_name = forms.CharField(
        label='Исполнитель',
        max_length=100,
        min_length=2,
        strip=True,
        error_messages={
            'required': 'Исполнитель обязателен.',
            'max_length': 'Имя исполнителя не должно превышать 100 символов.',
            'min_length': 'Имя исполнителя должно содержать минимум 2 символа.',
        }
    )
    signature_executor = forms.CharField(
        label='Подпись исполнителя',
        max_length=100,
        min_length=2,
        strip=True,
        error_messages={
            'required': 'Подпись исполнителя обязательна.',
            'max_length': 'Подпись исполнителя не должна превышать 100 символов.',
            'min_length': 'Подпись исполнителя должна содержать минимум 2 символа.',
        }
    )
    customer_name = forms.CharField(
        label='Заказчик',
        max_length=100,
        min_length=2,
        strip=True,
        error_messages={
            'required': 'Заказчик обязателен.',
            'max_length': 'Имя заказчика не должно превышать 100 символов.',
            'min_length': 'Имя заказчика должно содержать минимум 2 символа.',
        }
    )
    signature_customer = forms.CharField(
        label='Подпись заказчика',
        max_length=100,
        min_length=2,
        strip=True,
        error_messages={
            'required': 'Подпись заказчика обязательна.',
            'max_length': 'Подпись заказчика не должна превышать 100 символов.',
            'min_length': 'Подпись заказчика должна содержать минимум 2 символа.',
        }
    )
    subject = forms.CharField(
        label='Предмет договора',
        widget=forms.Textarea,
        min_length=10,
        strip=True,
        error_messages={
            'required': 'Предмет договора обязателен.',
            'min_length': 'Предмет договора должен содержать минимум 10 символов.',
        }
    )
    price = forms.DecimalField(
        label='Стоимость услуг',
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        error_messages={
            'required': 'Стоимость услуг обязательна.',
            'min_value': 'Стоимость услуг должна быть больше 0.',
            'max_digits': 'Стоимость услуг не должна превышать 10 цифр.',
            'invalid': 'Введите корректную сумму.',
        }
    )
    payment_terms = forms.CharField(
        label='Условия оплаты',
        widget=forms.Textarea,
        min_length=10,
        strip=True,
        error_messages={
            'required': 'Условия оплаты обязательны.',
            'min_length': 'Условия оплаты должны содержать минимум 10 символов.',
        }
    )
    contract_term = forms.DateField(
        label='Срок действия договора',
        input_formats=['%d.%m.%Y'],
        widget=forms.TextInput(attrs={'class': 'flatpickr', 'placeholder': 'дд.мм.гггг'}),
        error_messages={
            'required': 'Срок действия договора обязателен.',
            'invalid': 'Введите дату в формате дд.мм.гггг.',
        }
    )
    executor_details = forms.CharField(
        label='Реквизиты исполнителя',
        widget=forms.Textarea,
        min_length=10,
        strip=True,
        error_messages={
            'required': 'Реквизиты исполнителя обязательны.',
            'min_length': 'Реквизиты исполнителя должны содержать минимум 10 символов.',
        }
    )
    customer_details = forms.CharField(
        label='Реквизиты заказчика',
        widget=forms.Textarea,
        min_length=10,
        strip=True,
        error_messages={
            'required': 'Реквизиты заказчика обязательны.',
            'min_length': 'Реквизиты заказчика должны содержать минимум 10 символов.',
        }
    )
    contract_number = forms.CharField(
        label='Номер договора',
        max_length=100,
        min_length=1,
        strip=True,
        error_messages={
            'required': 'Номер договора обязателен.',
            'max_length': 'Номер договора не должен превышать 100 символов.',
            'min_length': 'Номер договора не может быть пустым.',
        }
    )

    def clean_city(self):
        city = self.cleaned_data['city']
        if not all(c.isalpha() or c.isspace() or c == '-' for c in city):
            raise forms.ValidationError('Город должен содержать только буквы, пробелы или дефисы.')
        return city

    def clean_contract_date(self):
        contract_date = self.cleaned_data['contract_date']
        if contract_date > timezone.now().date():
            raise forms.ValidationError('Дата договора не может быть в будущем.')
        return contract_date

    def clean_contract_term(self):
        contract_term = self.cleaned_data['contract_term']
        contract_date = self.cleaned_data.get('contract_date')
        if contract_date and contract_term <= contract_date:
            raise forms.ValidationError('Срок действия договора должен быть позже даты договора.')
        return contract_term

    def clean_contract_number(self):
        contract_number = self.cleaned_data['contract_number']
        if not contract_number.replace('-', '').replace('/', '').isalnum():
            raise forms.ValidationError('Номер договора должен содержать только буквы, цифры, дефисы или слэши.')
        return contract_number

    def clean_executor_name(self):
        executor_name = self.cleaned_data['executor_name']
        if not all(c.isalpha() or c.isspace() or c == '-' for c in executor_name):
            raise forms.ValidationError('Имя исполнителя должно содержать только буквы, пробелы или дефисы.')
        return executor_name

    def clean_customer_name(self):
        customer_name = self.cleaned_data['customer_name']
        if not all(c.isalpha() or c.isspace() or c == '-' for c in customer_name):
            raise forms.ValidationError('Имя заказчика должно содержать только буквы, пробелы или дефисы.')
        return customer_name



class DocumentForm(forms.ModelForm):
    creators = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Инициаторы (кроме вас)',
    )
    signers = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='Подписанты (кроме вас)',
        error_messages={
            'required': 'Укажите хотя бы одного подписанта.'
        }
    )

    class Meta:
        model = Document
        fields = ['title', 'description', 'creators', 'signers']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input mt-1 block w-full rounded-lg border-gray-300'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea mt-1 block w-full rounded-lg border-gray-300',
                'rows': 3
            })
        }
        error_messages = {
            'title': {
                'required': 'Название документа обязательно.',
                'max_length': 'Название документа не должно превышать 255 символов.'
            },
            'description': {
                'max_length': 'Описание не должно превышать 500 символов.'
            }
        }

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user')
        super().__init__(*args, **kwargs)
        self.fields['creators'].queryset = User.objects.exclude(id=self.current_user.id)
        self.fields['signers'].queryset = User.objects.exclude(id=self.current_user.id)

    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title.strip()) < 5:
            raise forms.ValidationError('Название документа должно содержать минимум 5 символов.')
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description') or ''
        if len(description.strip()) > 0 and len(description.strip()) < 10:
            raise forms.ValidationError('Описание, если указано, должно содержать минимум 10 символов.')
        return description

    def clean(self):
        cleaned_data = super().clean()
        signers = cleaned_data.get('signers')
        if not signers and not self.current_user in signers:
            self.add_error('signers', 'Укажите хотя бы одного подписанта.')
        return cleaned_data

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