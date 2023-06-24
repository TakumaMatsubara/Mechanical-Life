from . import views
from django.urls import path
from .views import google_auth, google_auth_callback

app_name = 'bot'

urlpatterns = [
    path('', views.callback, name='callback'),
    path('index', views.index, name='index'),
    path('auth/google/', google_auth, name='google_auth'),
    path('auth/google/callback/', google_auth_callback, name='google_auth_callback'),
]