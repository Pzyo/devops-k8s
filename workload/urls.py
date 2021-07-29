from django.conf.urls import url
from workload import views

urlpatterns = [
    url(r'^deployment$',views.deployment,name='workload_deployment'),
    url(r'^deployment_api$',views.deployment_api,name='workload_deployment_api'),
    url(r'^deployment_create$',views.deployment_create,name='workload_deployment_create'),
    url(r'^deployment_details$',views.deployment_details,name='workload_deployment_details'),
    url(r'^replicaset_api$',views.replicaset_api,name='replicaset_api'),
    url(r'^daemonset$',views.daemonset,name='workload_daemonset'),
    url(r'^daemonset_api$',views.daemonset_api,name='workload_daemonset_api'),
    url(r'^statefulset$',views.statefulset,name='workload_statefulset'),
    url(r'^statefulset_api$',views.statefulset_api,name='workload_statefulset_api'),
    url(r'^pod$', views.pod, name='workload_pod'),
    url(r'^pod_api$', views.pod_api, name='workload_pod_api'),
    url(r'^pod_log$', views.pod_log, name='workload_pod_log'),
    url(r'^pod_terminal$', views.pod_terminal, name='workload_pod_terminal'),
]