# horoscope_app/urls.py
from django.urls import path
from . import views
from .views import horoscope_detail

app_name = 'horoscope_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('horoscope/', views.horoscope, name='horoscope'),  # GET用のホロスコープAPI
    path('analyze/', views.analyze, name='analyze'),         # POSTで解析→OpenAI
    path('horoscope/detail/', horoscope_detail, name='horoscope_detail'),
    path('compatibility/', views.compatibility, name='compatibility'),
    path('analyze_compatibility/', views.analyze_compatibility, name='analyze_compatibility'),
]
