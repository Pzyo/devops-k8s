from django.conf.urls import url
from loadbalancer import views

urlpatterns = [
    url(r'^services$',views.services,name="loadbalancer_services"),
    url(r'^services_api$',views.services_api,name="loadbalancer_services_api"),
    url(r'^ingresses$',views.ingresses,name="loadbalancer_ingresses"),
    url(r'^ingresses_api$',views.ingresses_api,name="loadbalancer_ingresses_api"),
]