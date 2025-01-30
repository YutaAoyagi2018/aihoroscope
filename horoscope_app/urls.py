# horoscope_app/urls.py
from django.urls import path
from . import views

app_name = 'horoscope_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('horoscope/', views.horoscope, name='horoscope'),  # GET用のホロスコープAPI
    path('analyze/', views.analyze, name='analyze'),         # POSTで解析→OpenAI
]
