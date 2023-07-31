from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from django.urls import re_path
from devopsk8s.consumers import StreamConsumer

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter([
            re_path(r'^workload/terminal/(?P<namespace>.*)/(?P<pod_name>.*)/(?P<container>.*)/', StreamConsumer),
        ])
    ),
})