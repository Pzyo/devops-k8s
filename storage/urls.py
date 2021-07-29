from django.conf.urls import url
from storage import views

urlpatterns = [
    url(r'^persistentvolumeclaims$',views.persistentvolumeclaims,name='storage_persistentvolumeclaims'),
    url(r'^persistentvolumeclaims_api$',views.persistentvolumeclaims_api,name='storage_persistentvolumeclaims_api'),
    url(r'^configmap$',views.configmap,name='storage_configmap'),
    url(r'^configmap_api$',views.configmap_api,name='storage_configmap_api'),
    url(r'^secrets$',views.secrets,name='storage_secrets'),
    url(r'^secrets_api$',views.secrets_api,name='storage_secrets_api'),
]