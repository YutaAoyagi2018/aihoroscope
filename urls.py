from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.static import serve
import os

urlpatterns = [
    path('ads.txt', serve, {'path': 'ads.txt', 'document_root': os.path.join(settings.BASE_DIR, '..', 'aihoroscope')}),
    path('admin/', admin.site.urls),
    path('', include('horoscope_app.urls')),
]
