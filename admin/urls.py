from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('personnel/<str:personnel_id>/edit/', views.edit_personnel, name='edit_personnel'),
    path('items/register/', views.register_item, name='register_item'),
    path('settings/', views.system_settings, name='system_settings'),
]
