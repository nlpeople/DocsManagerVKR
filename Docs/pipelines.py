from django.contrib.auth.models import User
from .models import Profile


def create_user_profile(backend, user, response, *args, **kwargs):
    if backend.name == 'google-oauth2':
        # Проверяем, есть ли уже пользователи в системе
        is_first_user = User.objects.count() == 1

        profile, created = Profile.objects.get_or_create(user=user)

        if created:
            profile.first_name = response.get('given_name', user.first_name)
            profile.last_name = response.get('family_name', user.last_name)

            # Если это первый пользователь, назначаем его администратором
            if is_first_user:
                profile.role = 'admin'
            else:
                profile.role = 'employee'  # Роль по умолчанию - "сотрудник"

            profile.save()