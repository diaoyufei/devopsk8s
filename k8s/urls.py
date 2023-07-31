from django.urls import path, re_path, include
from k8s import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    re_path('^node/$', views.node, name="node"),
    re_path('^node_api/$', views.node_api, name="node_api"),
    re_path('^node_details/$', views.node_details, name="node_details"),
    re_path('^node_details_pod_list/$', views.node_details_pod_list, name="node_details_pod_list"),
    re_path('^pv/$', views.pv, name="pv"),
    re_path('^pv_create/$', views.pv_create, name="pv_create"),
    re_path('^pv_api/$', views.pv_api, name="pv_api"),
]