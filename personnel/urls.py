from django.urls import path
from .views import PersonnelListView, PersonnelDetailView

app_name = 'personnel'

urlpatterns = [
    path('', PersonnelListView.as_view(), name='personnel_profile_list'),
    path('<str:pk>/', PersonnelDetailView.as_view(), name='personnel_profile_detail'),
]

