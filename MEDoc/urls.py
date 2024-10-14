from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


admin_site = admin.site
admin_site.site_header = 'Администрирование MEDoc'
admin_site.site_title = 'Сайт администрирование MEDoc'


urlpatterns = [
    path('admin/', admin.site.urls),
    path('bots/', include('bots.urls')),
    path('documents/', include('docs.urls')),
    path('', include('profiles.urls'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
