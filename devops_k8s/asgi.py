import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from django.core.asgi import get_asgi_application
from django.conf.urls import url

from devops_k8s.consumers import StreamConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devops_k8s.settings')
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter([
            url(r'^workload/pod_terminal/(?P<namespace>.*)/(?P<pod_name>.*)/(?P<container>.*)/', StreamConsumer.as_asgi()),
        ])
    )
})