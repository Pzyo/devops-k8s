from django.shortcuts import render
from devops_k8s import k8s
from django.http import JsonResponse,QueryDict
from kubernetes import client
import datetime

# Create your views here.

@k8s.self_login_required
def services_api(request):
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
            core_api.delete_namespaced_service(name=name,namespace=namespace)
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
        for svc in core_api.list_namespaced_service(namespace=namespace).items:
            name = svc.metadata.name
            namespace = svc.metadata.namespace
            labels = svc.metadata.labels
            type = svc.spec.type
            cluster_ip = svc.spec.cluster_ip
            selector = svc.spec.selector

            ports = []
            for p in svc.spec.ports:
                port = p.port
                target_port = p.target_port
                protocol = p.protocol
                p_name = p.name

                node_port = "None"
                if type == "NodePort":
                    node_port = p.node_port

                p = {'node_port':node_port,'p_port':port,
                     'target_port':target_port,'p_protocol':protocol,
                     'p_name':p_name}
                ports.append(p)

            # 确认是否关联Pod
            endpoint = []
            for ep in core_api.list_namespaced_endpoints(namespace=namespace).items:
                print(ep)
                # if ep.metadata.name == name and ep.subsets is None:
                #     endpoint = "未关联"
                # elif ep.metadata.name == name and ep.subsets is not None:
                #     endpoint = "已关联"

                if ep.metadata.name == name and ep.subsets is not None:
                    for ep_addr in ep.subsets[0].addresses:
                        ep_ip = ep_addr.ip
                        endpoint.append(ep_ip)

            create_time = svc.metadata.creation_timestamp + datetime.timedelta(hours=8)
            create_time = datetime.datetime.strftime(create_time, '%Y-%m-%d %H:%M:%S')

            svc = {'name':name,'namespace':namespace,'labels':labels,
                   'type':type,'cluster_ip':cluster_ip,'selector':selector,
                   'svc_ports':ports,'endpoint':endpoint,'create_time':create_time}

            # 适配带条件查询, 搜索
            if search_key:
                if search_key in name:
                    data.append(svc)
            else:
                data.append(svc)
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
def services(request):
    return render(request, 'loadbalancer/services.html')

@k8s.self_login_required
def ingresses_api(request):
    auth_type = request.session.get('auth_type')
    token = request.session.get('token')
    namespace = request.GET.get('namespace', 'default')
    data = []
    k8s.load_auth_config(auth_type, token)

    net_api = client.NetworkingV1beta1Api()

    if request.method == 'DELETE':
        # 删除
        request_data = QueryDict(request.body)
        name = request_data.get('name')
        try:
            net_api.delete_namespaced_ingress(name=name,namespace=namespace)
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
        for ing in net_api.list_namespaced_ingress(namespace=namespace).items:
            # print(ing)
            name = ing.metadata.name
            namespace = ing.metadata.namespace
            labels = ing.metadata.labels

            http_hosts = []
            for h in ing.spec.rules:
                host = h.host
                # path = ("/" if h.http.paths[0].path else h.http.paths[0].path)
                # svc_name = h.http.paths[0].backend.service_name
                # svc_port = h.http.paths[0].backend.service_port
                path = []
                for p in h.http.paths:
                    p_path = p.path
                    p_svc_name = p.backend.service_name
                    p_svc_port = p.backend.service_port
                    p = {'p_path':p_path,'p_svc_name':p_svc_name,'p_svc_port':p_svc_port}
                    path.append(p)

                http_host = {'host':host,'path':path}
                              # 'svc_name':svc_name,'svc_port':svc_port}
                http_hosts.append(http_host)

            https_hosts = "None"
            if ing.spec.tls is None:
                https_hosts = ing.spec.tls
            else:
                for tls in ing.spec.tls:
                    host = tls.hosts[0]
                    secret_name = tls.secret_name
                    https_hosts = {'host': host, 'secret_name': secret_name}

            create_time = ing.metadata.creation_timestamp + datetime.timedelta(hours=8)
            create_time = datetime.datetime.strftime(create_time, '%Y-%m-%d %H:%M:%S')

            ing = {'name':name,'namespace':namespace,'labels':labels,
                   'http_hosts':http_hosts,'https_hosts':https_hosts,
                   'create_time':create_time}

            # 适配带条件查询, 搜索
            if search_key:
                if search_key in name:
                    data.append(ing)
            else:
                data.append(ing)
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
def ingresses(request):
    return render(request, 'loadbalancer/ingresses.html')