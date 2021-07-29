from django.shortcuts import render
from devops_k8s import k8s
import datetime
from kubernetes import client
from django.http import JsonResponse, QueryDict

# Create your views here.

@k8s.self_login_required
def persistentvolumeclaims_api(request):
    auth_type = request.session.get('auth_type')
    token = request.session.get('token')
    namespace = request.GET.get('namespace', 'default')
    data = []
    k8s.load_auth_config(auth_type, token)

    core_api = client.CoreV1Api()

    if request.method == 'DELETE':
        # 删除
        request_data = QueryDict(request.body)
        name = request_data.get('name')
        try:
            core_api.delete_namespaced_persistent_volume_claim(name=name,namespace=namespace)
            code = 0
            msg = "删除成功!"
        except Exception as e:
            status = getattr(e, 'status')
            if status == 403:
                msg = "没有访问权限!"
            else:
                msg = "删除失败!"
            code = 1
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)

    elif request.method == 'POST':
        # 新增
        pass

    search_key = request.GET.get('search_key')
    try:
        for pvc in core_api.list_namespaced_persistent_volume_claim(namespace=namespace).items:
            # print(pvc)
            name = pvc.metadata.name
            namespace = pvc.metadata.namespace
            labels = pvc.metadata.labels
            access_modes = pvc.spec.access_modes
            capacity = (pvc.status.capacity["storage"] if pvc.status.capacity else pvc.status.capacity)
            volume_name = pvc.spec.volume_name
            status = pvc.status.phase
            storage_class_name = pvc.spec.storage_class_name

            create_time = pvc.metadata.creation_timestamp + datetime.timedelta(hours=8)
            create_time = datetime.datetime.strftime(create_time, '%Y-%m-%d %H:%M:%S')

            pvc = {'name':name,'namespace':namespace,'labels':labels,
                   'access_modes':access_modes,'capacity':capacity,
                   'volume_name':volume_name,'status':status,
                   'storage_class_name':storage_class_name,
                   'create_time':create_time}

            # 适配带条件查询, 搜索
            if search_key:
                if search_key in name:
                    data.append(pvc)
            else:
                data.append(pvc)
        code = 0
        msg = "查询成功!"
    except Exception as e:
        status = getattr(e, 'status')
        if status == 403:
            msg = "没有访问权限!"
        else:
            msg = "查询失败!"
        code = 1
    count = len(data)

    current_page = request.GET.get('page', 1)
    page_item_num = request.GET.get('limit', 10)

    try:
        current_page = int(current_page)
        page_item_num = int(page_item_num)
    except Exception:
        current_page = 1
        page_item_num = 10

    start = (current_page - 1) * page_item_num
    end = current_page * page_item_num
    data = data[start:end]
    res = {'code': code, 'msg': msg, 'data': data, 'count': count}
    return JsonResponse(res)

@k8s.self_login_required
def persistentvolumeclaims(request):
    return render(request, 'storage/persistentvolumeclaims.html')

@k8s.self_login_required
def configmap_api(request):
    auth_type = request.session.get('auth_type')
    token = request.session.get('token')
    namespace = request.GET.get('namespace', 'default')
    data = []
    k8s.load_auth_config(auth_type, token)

    core_api = client.CoreV1Api()

    if request.method == 'DELETE':
        # 删除
        request_data = QueryDict(request.body)
        name = request_data.get('name')
        try:
            core_api.delete_namespaced_config_map(name=name,namespace=namespace)
            code = 0
            msg = "删除成功!"
        except Exception as e:
            status = getattr(e, 'status')
            if status == 403:
                msg = "没有访问权限!"
            else:
                msg = "删除失败!"
            code = 1
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)

    elif request.method == 'POST':
        # 新增
        pass

    search_key = request.GET.get('search_key')
    try:
        for cm in core_api.list_namespaced_config_map(namespace=namespace).items:
            # print(cm)
            name = cm.metadata.name
            namespace = cm.metadata.namespace
            labels = cm.metadata.labels
            data_length = (len(cm.data) if cm.data else "0")
            create_time = cm.metadata.creation_timestamp + datetime.timedelta(hours=8)
            create_time = datetime.datetime.strftime(create_time, '%Y-%m-%d %H:%M:%S')

            cm = {'name':name,'namespace':namespace,'labels':labels,
                   'data_length':data_length,'create_time':create_time}

            # 适配带条件查询, 搜索
            if search_key:
                if search_key in name:
                    data.append(cm)
            else:
                data.append(cm)
        code = 0
        msg = "查询成功!"
    except Exception as e:
        status = getattr(e, 'status')
        if status == 403:
            msg = "没有访问权限!"
        else:
            msg = "查询失败!"
        code = 1
    count = len(data)

    current_page = request.GET.get('page', 1)
    page_item_num = request.GET.get('limit', 10)

    try:
        current_page = int(current_page)
        page_item_num = int(page_item_num)
    except Exception:
        current_page = 1
        page_item_num = 10

    start = (current_page - 1) * page_item_num
    end = current_page * page_item_num
    data = data[start:end]
    res = {'code': code, 'msg': msg, 'data': data, 'count': count}
    return JsonResponse(res)

@k8s.self_login_required
def configmap(request):
    return render(request, 'storage/configmap.html')

@k8s.self_login_required
def secrets_api(request):
    auth_type = request.session.get('auth_type')
    token = request.session.get('token')
    namespace = request.GET.get('namespace', 'default')
    data = []
    k8s.load_auth_config(auth_type, token)

    core_api = client.CoreV1Api()

    if request.method == 'DELETE':
        # 删除
        request_data = QueryDict(request.body)
        name = request_data.get('name')
        try:
            core_api.delete_namespaced_secret(name=name,namespace=namespace)
            code = 0
            msg = "删除成功!"
        except Exception as e:
            status = getattr(e, 'status')
            if status == 403:
                msg = "没有访问权限!"
            else:
                msg = "删除失败!"
            code = 1
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)

    elif request.method == 'POST':
        # 新增
        pass

    search_key = request.GET.get('search_key')
    try:
        for secret in core_api.list_namespaced_secret(namespace=namespace).items:
            print(secret)
            name = secret.metadata.name
            namespace = secret.metadata.namespace
            labels = secret.metadata.labels
            data_length = (len(secret.data) if secret.data else "0")
            type = secret.type
            create_time = secret.metadata.creation_timestamp + datetime.timedelta(hours=8)
            create_time = datetime.datetime.strftime(create_time, '%Y-%m-%d %H:%M:%S')

            secret = {'name':name,'namespace':namespace,'labels':labels,
                    'data_length':data_length,'type':type,
                   'create_time':create_time}

            # 适配带条件查询, 搜索
            if search_key:
                if search_key in name:
                    data.append(secret)
            else:
                data.append(secret)
        code = 0
        msg = "查询成功!"
    except Exception as e:
        status = getattr(e, 'status')
        if status == 403:
            msg = "没有访问权限!"
        else:
            msg = "查询失败!"
        code = 1
    count = len(data)

    current_page = request.GET.get('page', 1)
    page_item_num = request.GET.get('limit', 10)

    try:
        current_page = int(current_page)
        page_item_num = int(page_item_num)
    except Exception:
        current_page = 1
        page_item_num = 10

    start = (current_page - 1) * page_item_num
    end = current_page * page_item_num
    data = data[start:end]
    res = {'code': code, 'msg': msg, 'data': data, 'count': count}
    return JsonResponse(res)

@k8s.self_login_required
def secrets(request):
    return render(request, 'storage/secrets.html')