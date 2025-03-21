# horoscope_app/urls.py
from django.urls import path
from . import views
from .views import horoscope_detail
from django.views.generic import TemplateView

app_name = 'horoscope_app'

urlpatterns = [
    path('ads.txt', TemplateView.as_view(
        template_name='ads.txt',
        content_type='text/plain'
    )),
    path('', views.index, name='index'),
    path('horoscope/', views.horoscope, name='horoscope'),  # GET用のホロスコープAPI
    path('horoscope/ai/', views.horoscope_ai, name='horoscope_ai'),  # AI用のホロスコープAPI
    path('analyze/', views.analyze, name='analyze'),         # POSTで解析→OpenAI
    path('horoscope/detail/', horoscope_detail, name='horoscope_detail'),
    path('compatibility/', views.compatibility, name='compatibility'),
    path('analyze_compatibility/', views.analyze_compatibility, name='analyze_compatibility'),
]
