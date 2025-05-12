from django.contrib import admin
from .models import Document, DocumentFile, Profile, DocumentSignature, DocumentTemplate, DocumentComment
# Register your models here.
admin.site.register(Profile)
admin.site.register(DocumentFile)
admin.site.register(Document)
admin.site.register(DocumentSignature)
admin.site.register(DocumentTemplate)
admin.site.register(DocumentComment)
