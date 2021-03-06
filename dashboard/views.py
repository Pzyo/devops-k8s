from django.shortcuts import render,redirect
from django.http import JsonResponse
from devops_k8s.k8s import auth_check, self_login_required, load_auth_config, dt_format
import hashlib, random
from dashboard.models import User
from kubernetes import client
from dashboard import node_data

@self_login_required
def index(request):
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    # 命名空间：ajax从接口获取动态渲染
    # 计算资源（echart）：ajax从接口获取动态渲染
    # 存储资源：下面获取，模板渲染
    # 节点状态：下面获取，模板渲染

    node_resource = node_data.node_resource(core_api)
    pv_list = []
    for pv in core_api.list_persistent_volume().items:
        pv_name = pv.metadata.name
        capacity = pv.spec.capacity["storage"]  # 返回字典对象
        access_modes = pv.spec.access_modes
        reclaim_policy = pv.spec.persistent_volume_reclaim_policy
        status = pv.status.phase
        if pv.spec.claim_ref is not None:
            pvc_ns = pv.spec.claim_ref.namespace
            pvc_name = pv.spec.claim_ref.name
            claim = "%s/%s" %(pvc_ns,pvc_name)
        else:
            claim = "未关联PVC"
        storage_class = pv.spec.storage_class_name
        create_time = dt_format(pv.metadata.creation_timestamp)

        data = {"pv_name": pv_name, "capacity": capacity, "access_modes": access_modes,
                "reclaim_policy": reclaim_policy, "status": status,
                "claim": claim,"storage_class": storage_class,"create_time": create_time}
        pv_list.append(data)

    return render(request, 'index.html', {"node_resource": node_resource, "pv_list": pv_list})

# 计算资源（echart）
def node_resource(request):
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    res = node_data.node_resource(core_api)
    return JsonResponse(res)

def login(request):
    if request.method == 'POST':
        print(request.POST)
        # 处理token登录
        token = request.POST.get('token')
        if token:  # 判断token是否为空
            # 判断token的可用性
            if auth_check(auth_type='token', token=token):
                request.session['is_login'] = True
                request.session['token'] = token
                request.session['auth_type'] = 'token'
                code = 0
                msg = "登录成功"
            else:
                code = 1
                msg = "token无效"
        else:
        # 处理kubeconfig登录
            file_obj = request.FILES.get('file')
            # 生成一个随机字符串(token), 保存到session, 用于标识登录用户
            token_random = hashlib.md5(str(random.random()).encode()).hexdigest()
            try:
                content = file_obj.read().decode()  # bytes to str
                User.objects.create(
                    auth_type='kubeconfig',
                    token=token_random,
                    content=content
                )
            except Exception as e:
                print(e)
                code = 1
                msg = "文件类型错误"
            if auth_check(auth_type='kubeconfig', token=token_random):
                request.session['is_login'] = True
                request.session['token'] = token_random
                request.session['auth_type'] = 'kubeconfig'
                code = 0
                msg = "登录成功"
            else:
                code = 1
                msg = "kubeconfig文件无效"
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)
    return render(request, 'login.html')

def logout(request):
    request.session.flush()
    return redirect(login)

@self_login_required
def export_resource_api(request):
    namespace = request.GET.get('namespace')
    resource = request.GET.get('resource')
    name = request.GET.get('name')

    # 认证相关
    auth_type = request.session.get('auth_type')
    token = request.session.get('token')
    load_auth_config(auth_type, token)

    core_api = client.CoreV1Api()  # namespace,pod,service,pv,pvc
    apps_api = client.AppsV1Api()  # deployment,daemonset,statefulset
    net_api = client.NetworkingV1beta1Api() # ingress
    storage_api = client.StorageV1Api() # storage_class

    import yaml,json

    yaml_str = ""
    if resource == 'deployment':
        try:
            res_str = apps_api.read_namespaced_deployment(name=name, namespace=namespace, _preload_content=False).read().decode() # byte -> str
            json_str = json.loads(res_str) # str -> json
            yaml_str = yaml.safe_dump(json_str)  # json -> yaml
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'namespace':
        try:
            res_str = core_api.read_namespace(name=name, _preload_content=False).read().decode()
            json_str = json.loads(res_str)
            yaml_str = yaml.safe_dump(json_str)
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'persistentvolumes':
        try:
            res_str = core_api.read_persistent_volume(name=name, _preload_content=False).read().decode()
            json_str = json.loads(res_str)
            yaml_str = yaml.safe_dump(json_str)
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'pods':
        try:
            res_str = core_api.read_namespaced_pod(name=name, namespace=namespace , _preload_content=False).read().decode()
            json_str = json.loads(res_str)
            yaml_str = yaml.safe_dump(json_str)
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'daemonset':
        try:
            res_str = apps_api.read_namespaced_daemon_set(name=name, namespace=namespace , _preload_content=False).read().decode()
            json_str = json.loads(res_str)
            yaml_str = yaml.safe_dump(json_str)
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'statefulset':
        try:
            res_str = apps_api.read_namespaced_stateful_set(name=name, namespace=namespace , _preload_content=False).read().decode()
            json_str = json.loads(res_str)
            yaml_str = yaml.safe_dump(json_str)
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'service':
        try:
            res_str = core_api.read_namespaced_service(name=name, namespace=namespace , _preload_content=False).read().decode()
            json_str = json.loads(res_str)
            yaml_str = yaml.safe_dump(json_str)
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'ingress':
        try:
            res_str = net_api.read_namespaced_ingress(name=name, namespace=namespace , _preload_content=False).read().decode()
            json_str = json.loads(res_str)
            yaml_str = yaml.safe_dump(json_str)
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'persistentvolumeclaim':
        try:
            res_str = core_api.read_namespaced_persistent_volume_claim(name=name, namespace=namespace , _preload_content=False).read().decode()
            json_str = json.loads(res_str)
            yaml_str = yaml.safe_dump(json_str)
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'configmap':
        try:
            res_str = core_api.read_namespaced_config_map(name=name, namespace=namespace , _preload_content=False).read().decode()
            json_str = json.loads(res_str)
            yaml_str = yaml.safe_dump(json_str)
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'secret':
        try:
            res_str = core_api.read_namespaced_secret(name=name, namespace=namespace , _preload_content=False).read().decode()
            json_str = json.loads(res_str)
            yaml_str = yaml.safe_dump(json_str)
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'node':
        try:
            res_str = core_api.read_node(name=name, _preload_content=False).read().decode()
            json_str = json.loads(res_str)
            yaml_str = yaml.safe_dump(json_str)
        except Exception as e:
            code = 1
            msg = e
    elif resource == 'replicaset':
        try:
            res_str = apps_api.read_namespaced_replica_set(name=name, namespace=namespace, _preload_content=False).read().decode()
            json_str = json.loads(res_str)
            yaml_str = yaml.safe_dump(json_str)
        except Exception as e:
            code = 1
            msg = e
    else:
        code = 1
        msg = "未配置%s资源类型!"%(resource)

    code = 0
    msg = "查看YAML成功!"
    res = {"code":code,"msg":msg,"data":yaml_str}
    return JsonResponse(res)

from django.views.decorators.clickjacking import xframe_options_sameorigin

@self_login_required
@xframe_options_sameorigin
def ace(request):
    namespace = request.GET.get('namespace')
    resource = request.GET.get('resource')
    name = request.GET.get('name')

    data = {}
    data['namespace'] = namespace
    data['resource'] = resource
    data['name'] = name

    return render(request, 'ace.html', {'data':data})