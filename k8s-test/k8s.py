from kubernetes import client, config
import os

kubeconfig = os.path.join(os.getcwd(), 'config')
config.load_kube_config(kubeconfig)
apps_api = client.AppsV1Api()
pod_api = client.CoreV1Api()

for dp in apps_api.list_deployment_for_all_namespaces().items:
    print(dp)