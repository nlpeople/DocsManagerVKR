from django.contrib.auth.models import User
from .models import Profile

def create_user_profile(backend, user, response, *args, **kwargs):
    if backend.name == 'google-oauth2':
        profile, created = Profile.objects.get_or_create(user=user)

        if created:
            profile.first_name = response.get('given_name', user.first_name)
            profile.last_name = response.get('family_name', user.last_name)
            profile.role = 'employee'  # Роль по умолчанию - "сотрудник"

            picture = response.get('picture')
            if picture:
                profile.photo = picture  # Здесь лучше использовать сохранение изображения

            profile.save()
