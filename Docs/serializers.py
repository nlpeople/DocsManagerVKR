from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Document, DocumentFile


class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # Отображаем имя пользователя

    class Meta:
        model = Profile
        fields = '__all__'


class DocumentSerializer(serializers.ModelSerializer):
    creators = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    signers = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    signed_by = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)

    class Meta:
        model = Document
        fields = '__all__'


class DocumentFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentFile
        fields = '__all__'
