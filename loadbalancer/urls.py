from django.urls import path, re_path, include
from loadbalancer import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    re_path('^service/$', views.service, name="service"),
    re_path('^service_api/$', views.service_api, name="service_api"),
    re_path('^ingress/$', views.ingress, name="ingress"),
    re_path('^ingress_api/$', views.ingress_api, name="ingress_api"),
]