from django.contrib import admin
from django.urls import path, include
from django.conf import settings                  # ✅ FIXED
from django.conf.urls.static import static        # ✅ FIXED

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('qrmenu.urls')),  # or your app name
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

