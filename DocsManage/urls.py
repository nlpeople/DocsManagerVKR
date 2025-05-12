from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from Docs import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.http import HttpResponse

docspatterns = [
    path('', views.document_list, name='document_list'),
    path('delete/<int:pk>/', views.delete_document, name='delete_document'),
    path('create/', views.create_document, name='create_document'),
    path('select_document_type/', views.select_document_type, name='select_document_type'),
    path('create_templated/<str:document_type>/', views.create_templated_document, name='create_templated_document'),
    path('edit/<int:pk>/', views.edit_document, name='edit_document'),
    path('file/delete/<int:file_id>/', views.delete_file, name='delete_file'),
    path('<int:pk>/', views.document_detail, name='document_detail'),
    path('document_created/', views.document_created, name='document_created'),
    path('export/pdf/', views.export_documents_pdf, name='export_documents_pdf'),
    path('<int:pk>/comments/', views.document_comments, name='document_comments'),
]

urlpatterns = [
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/change-role/', views.admin_change_role, name='admin_change_role'),
    path('metrics/', views.prometheus_metrics, name='prometheus_metrics'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='edit_profile'),
    path("docs/", include(docspatterns)),
    path("bind_telegram/", views.bind_telegram, name="bind_telegram"),
    path('unbind_telegram/', views.unbind_telegram, name='unbind_telegram'),
    path('admin/', admin.site.urls),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path("", views.home, name='index'),
    path('login/', views.login_disabled_view, name='login'),
    path('admin-panel/backup/', views.backup_dashboard, name='backup_dashboard'),
    path('admin-panel/backup/export/csv/', views.export_csv_backup, name='export_csv_backup'),
    path('admin-panel/backup/export/sql/', views.export_sql_backup, name='export_sql_backup'),
    path('admin-panel/backup/import/csv/', views.import_csv_backup, name='import_csv_backup'),
    path('admin-panel/backup/import/sql/', views.import_sql_backup, name='import_sql_backup'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)