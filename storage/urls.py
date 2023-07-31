from django.urls import path, re_path, include
from storage import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    re_path('^pvc/$', views.pvc, name="pvc"),
    re_path('^pvc_api/$', views.pvc_api, name="pvc_api"),
    re_path('^configmap/$', views.configmap, name="configmap"),
    re_path('^configmap_api/$', views.configmap_api, name="configmap_api"),
    re_path('^secret/$', views.secret, name="secret"),
    re_path('^secret_api/$', views.secret_api, name="secret_api"),
]