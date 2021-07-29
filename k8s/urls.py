from django.conf.urls import url
from k8s import views

urlpatterns = [
    url(r'^namespace_api$',views.namespace_api,name="k8s_namespace_api"),
    url(r'^namespace$',views.namespace,name="k8s_namespace"),
    url(r'^node$',views.node,name="k8s_node"),
    url(r'^node_api$',views.node_api,name="k8s_node_api"),
    url(r'^node_detail$',views.node_detail,name="k8s_node_detail"),
    url(r'^node_detail_pod_list$',views.node_detail_pod_list,name="k8s_node_detail_pod_list"),
    url(r'^pv$',views.pv,name="k8s_pv"),
    url(r'^pv_api$',views.pv_api,name="k8s_pv_api"),
    url(r'^pv_create$',views.pv_create,name="k8s_pv_create"),
]