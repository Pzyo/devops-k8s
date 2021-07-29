from django.shortcuts import render
from django.http import JsonResponse, QueryDict
from devops_k8s import k8s
from kubernetes import client
import datetime

# Create your views here.

@k8s.self_login_required
def deployment_api(request):
    auth_type = request.session.get('auth_type')
    token = request.session.get('token')
    namespace = request.GET.get('namespace', 'default')
    data = []
    k8s.load_auth_config(auth_type, token)

    apps_api = client.AppsV1Api()

    if request.method == 'DELETE':
        # 删除
        request_data = QueryDict(request.body)
        name = request_data.get('name')
        try:
            apps_api.delete_namespaced_deployment(name=name,namespace=namespace)
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

    elif request.method == 'PUT':
        request_data = QueryDict(request.body)
        replicas = int(request_data.get('replicas'))
        name = request_data.get('name')
        namespace = request_data.get('namespace')

        try:
            body = apps_api.read_namespaced_deployment(name=name, namespace=namespace)
            current_replicas = body.spec.replicas
            min_replicas = 0
            max_replicas = 20

            if replicas > current_replicas and replicas < max_replicas:
                body.spec.replicas = replicas
                apps_api.patch_namespaced_deployment(name=name, namespace=namespace, body=body)
                code = 0
                msg = '扩容成功!'
            elif replicas < current_replicas and replicas > min_replicas:
                body.spec.replicas = replicas
                apps_api.patch_namespaced_deployment(name=name, namespace=namespace, body=body)
                code = 0
                msg = '缩容成功!'
            elif replicas == current_replicas:
                code = 1
                msg = '副本数一致!'
            elif replicas > max_replicas:
                code = 1
                msg = '副本数过大, 请少于20!'
            elif replicas <= min_replicas:
                code = 1
                msg = '副本数过小, 请大于0!'
        except Exception as e:
            status = getattr(e, 'status')
            if status == 403:
                msg = "没有访问权限!"
            else:
                msg = "伸缩失败!"
            code = 1

        res = {'code': code, 'msg': msg}
        return JsonResponse(res)

    elif request.method == 'POST':
        deployName = request.POST.get('deployName')
        deployLabels = request.POST.get('deployLabels', None)
        imageName = request.POST.get('imageName')
        imagesTag = request.POST.get('imagesTag', 'latest')
        imagePullPolicy = request.POST.get('imagePullPolicy', 'IfNotPresent')
        namespace = request.POST.get('namespace', 'default')
        replicas = request.POST.get('replicas', 1)
        ureplicas = request.POST.get('ureplicas', None)
        limitCpu = request.POST.get('limitCpu', None)
        limitMem = request.POST.get('limitMem', None)
        requestCpu = request.POST.get('requestCpu', None)
        requestMem = request.POST.get('requestMem', None)

        try:
            labels = {}
            for l in deployLabels.split(","):
                k = l.split(':')[0]
                v = l.split(':')[1]
                labels[k] = v
        except Exception:
            res = {'code': 1, 'msg': "标签格式错误!"}
            return JsonResponse(res)

        if imagesTag:
            image = ':'.join((imageName,imagesTag))
        else:
            image = ':'.join((imageName, 'latest'))
        # print(image)

        limits = {}
        if limitCpu:
            limits['cpu'] = limitCpu
        if limitMem:
            limits['memory'] = limitMem

        requests = {}
        if requestCpu:
            requests['cpu'] = requestCpu
        if requestMem:
            requests['memory'] = requestMem

        body = client.V1Deployment(
            api_version='apps/v1'
            ,kind='Deployment'
            ,metadata=client.V1ObjectMeta(
                name=deployName
                ,labels=labels
            )
            ,spec=client.V1DeploymentSpec(
                replicas=(int(ureplicas) if replicas == '自定义' else int(replicas))
                ,selector=client.V1LabelSelector(
                    match_labels=labels
                )
                ,template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels=labels
                    )
                    ,spec=client.V1PodSpec(
                        containers=[client.V1Container(
                            name=imageName
                            ,image = image
                            ,image_pull_policy=imagePullPolicy
                            ,resources = client.V1ResourceRequirements(
                                limits = limits
                                ,requests = requests
                            )
                        )]
                    )
                )
            )
        )

        try:
            apps_api.create_namespaced_deployment(namespace=namespace, body=body)
            code = 0
            msg = "创建Deployment成功!"
        except Exception as e:
            print(e)
            status = getattr(e, 'status')
            if status == 403:
                msg = "没有创建权限!"
            else:
                msg = "创建Deployment失败!"
            code = 1

        res = {'code': code, 'msg': msg}
        return JsonResponse(res)

    search_key = request.GET.get('search_key')
    try:
        for deploy in apps_api.list_namespaced_deployment(namespace=namespace).items:
            name = deploy.metadata.name
            namespace = deploy.metadata.namespace
            replicas = deploy.spec.replicas
            available_replicas = (0 if deploy.status.available_replicas is None else deploy.status.available_replicas)
            labels = deploy.metadata.labels
            selector = deploy.spec.selector.match_labels
            containers = {}
            for c in deploy.spec.template.spec.containers:
                containers[c.name] = c.image
            create_time = deploy.metadata.creation_timestamp + datetime.timedelta(hours=8)
            create_time = datetime.datetime.strftime(create_time, '%Y-%m-%d %H:%M:%S')

            deploy = {'name':name,'namespace':namespace,'labels':labels,
                      'replicas': '%s / %s'%(available_replicas,replicas),
                      'mreplicas': replicas,
                      'selector':selector,'containers':containers,
                      'create_time':create_time}

            # 适配带条件查询, 搜索
            if search_key:
                if search_key in name:
                    data.append(deploy)
            else:
                data.append(deploy)
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
def deployment(request):
    return render(request, 'workload/deployment.html')

@k8s.self_login_required
def deployment_details(request):
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)

    core_api = client.CoreV1Api()
    apps_api = client.AppsV1Api()
    networking_api = client.NetworkingV1beta1Api()

    dp_name = request.GET.get("name")
    namespace = request.GET.get("namespace")

    dp_info = []
    for dp in apps_api.list_namespaced_deployment(namespace=namespace).items:
        if dp_name == dp.metadata.name:
            name = dp.metadata.name
            namespace = dp.metadata.namespace
            replicas = dp.spec.replicas
            available_replicas = ( 0 if dp.status.available_replicas is None else dp.status.available_replicas) # ready_replicas
            labels = dp.metadata.labels
            selector = dp.spec.selector.match_labels

            # 通过deployment反查对应service
            service = []
            svc_name = None
            for svc in core_api.list_namespaced_service(namespace=namespace).items:
                if svc.spec.selector == selector:
                    svc_name = svc.metadata.name  # 通过该名称筛选ingress
                    type = svc.spec.type
                    cluster_ip = svc.spec.cluster_ip
                    ports = svc.spec.ports

                    data = {"type": type, "cluster_ip": cluster_ip, "ports": ports}
                    service.append(data)

            # service没有创建，ingress也就没有  ingress->service->deployment->pod
            ingress = {"rules": None,"tls": None}
            for ing in networking_api.list_namespaced_ingress(namespace=namespace).items:
                for r in ing.spec.rules:
                    for b in r.http.paths:
                        if b.backend.service_name == svc_name:
                            ingress["rules"] = ing.spec.rules
                            ingress["tls"] = ing.spec.tls

            containers = []
            for c in dp.spec.template.spec.containers:
                c_name = c.name
                image = c.image
                liveness_probe = c.liveness_probe
                readiness_probe = c.readiness_probe
                resources = c.resources  # 在前端处理
                env = c.env
                ports = c.ports
                volume_mounts = c.volume_mounts
                args = c.args
                command = c.command

                container = {"name":c_name, "image": image ,"liveness_probe": liveness_probe, "readiness_probe": readiness_probe,
                             "resources": resources, "env": env, "ports":ports,
                             "volume_mounts": volume_mounts, "args": args, "command": command}
                containers.append(container)

            tolerations = dp.spec.template.spec.tolerations
            rolling_update = dp.spec.strategy.rolling_update
            volumes = []
            if dp.spec.template.spec.volumes is not None:
                for v in dp.spec.template.spec.volumes:  # 返回类似字典格式，不知道为啥不能遍历
                    volume = {}
                    if v.config_map is not None:
                        volume["config_map"] = v.config_map
                    elif v.secret is not None:
                        volume["secret"] = v.secret
                    elif v.empty_dir is not None:
                        volume["empty_dir"] = v.empty_dir
                    elif v.host_path is not None:
                        volume["host_path"] = v.host_path
                    elif v.config_map is not None:
                        volume["downward_api"] = v.downward_api
                    elif v.config_map is not None:
                        volume["glusterfs"] = v.glusterfs
                    elif v.cephfs is not None:
                        volume["cephfs"] = v.cephfs
                    elif v.rbd is not None:
                        volume["rbd"] = v.rbd
                    elif v.persistent_volume_claim is not None:
                        volume["persistent_volume_claim"] = v.persistent_volume_claim
                    else:
                        volume["unknown"] = "unknown"
                    volumes.append(volume)

            rs_number = dp.spec.revision_history_limit
            create_time = k8s.dt_format(dp.metadata.creation_timestamp)

            dp_info = {"name": name, "namespace": namespace, "replicas": replicas,
                       "available_replicas": available_replicas, "labels": labels,
                       "selector": selector, "containers": containers, "rs_number":rs_number,
                       "rolling_update":rolling_update,"create_time": create_time, "volumes":volumes,
                       "tolerations":tolerations,"service":service, "ingress":ingress}

    return render(request, 'workload/deployment_details.html', {'dp_name':dp_name, 'namespace': namespace, 'dp_info': dp_info})

@k8s.self_login_required
def replicaset_api(request):
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)

    apps_api = client.AppsV1Api()
    apps_beta_api = client.ExtensionsV1beta1Api()

    if request.method == "GET":
        dp_name = request.GET.get("name", None)
        namespace = request.GET.get("namespace", None)
        data = []
        for rs in apps_api.list_namespaced_replica_set(namespace=namespace).items:
            current_dp_name = rs.metadata.owner_references[0].name
            rs_name = rs.metadata.name
            if dp_name == current_dp_name:
                namespace = rs.metadata.namespace
                replicas = rs.status.replicas
                available_replicas = rs.status.available_replicas
                ready_replicas = rs.status.ready_replicas
                revision = rs.metadata.annotations["deployment.kubernetes.io/revision"]
                create_time = rs.metadata.creation_timestamp

                containers = {}
                for c in rs.spec.template.spec.containers:
                    containers[c.name] = c.image

                rs = {"name": rs_name, "namespace": namespace, "replicas": replicas,
                        "available_replicas": available_replicas, "ready_replicas": ready_replicas,
                        "revision":revision, 'containers': containers, "create_time": create_time}
                data.append(rs)
        count = len(data) # 可选，rs默认保存10条，所以不用分页
        res = {"code": 0, "msg": "", "count": count, 'data': data}
        return JsonResponse(res)
    elif request.method == "POST":

        dp_name = request.POST.get("dp_name", None)  # deployment名称
        namespace = request.POST.get("namespace", None)
        revision = request.POST.get("revision", None)
        # body = {"name": dp_name, "rollback_to": {"revision": revision}}
        body = {'revision': int(revision)}

        try:
            # apps_beta_api.create_namespaced_deployment_rollback(name=dp_name, namespace=namespace, body=body)
            apps_api.patch_namespaced_controller_revision(name=dp_name,namespace=namespace, body=body)
            code = 0
            msg = "回滚成功！"
        except Exception as e:
            print(e)
            status = getattr(e, "status")
            if status == 403:
                msg = "你没有回滚权限！"
            else:
                msg = "回滚失败！"
            code = 1
        res = {"code": code, "msg": msg}
        return JsonResponse(res)

from django.views.decorators.clickjacking import xframe_options_sameorigin

@k8s.self_login_required
@xframe_options_sameorigin
def deployment_create(request):
    return render(request, 'workload/deployment_create.html')

@k8s.self_login_required
def daemonset_api(request):
    auth_type = request.session.get('auth_type')
    token = request.session.get('token')
    namespace = request.GET.get('namespace', 'default')
    data = []
    k8s.load_auth_config(auth_type, token)

    apps_api = client.AppsV1Api()

    if request.method == 'DELETE':
        # 删除
        request_data = QueryDict(request.body)
        name = request_data.get('name')
        try:
            apps_api.delete_namespaced_daemon_set(name=name,namespace=namespace)
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
        for ds in apps_api.list_namespaced_daemon_set(namespace=namespace).items:
            name = ds.metadata.name
            namespace = ds.metadata.namespace
            labels = ds.metadata.labels
            desired_number = ds.status.desired_number_scheduled
            available_number = (0 if ds.status.number_available is None else ds.status.number_available)
            selector = ds.spec.selector.match_labels
            containers = {}
            for c in ds.spec.template.spec.containers:
                containers[c.name] = c.image
            create_time = ds.metadata.creation_timestamp + datetime.timedelta(hours=8)
            create_time = datetime.datetime.strftime(create_time ,'%Y-%m-%d %H:%M:%S')

            ds = {'name':name,'namespace':namespace,'labels':labels,
                  'replicas': '%s / %s'%(available_number, desired_number),
                  'selector':selector,'containers':containers,
                  'create_time':create_time}

            # 适配带条件查询, 搜索
            if search_key:
                if search_key in name:
                    data.append(ds)
            else:
                data.append(ds)
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
def daemonset(request):
    return render(request, 'workload/daemonset.html')

@k8s.self_login_required
def statefulset_api(request):
    auth_type = request.session.get('auth_type')
    token = request.session.get('token')
    namespace = request.GET.get('namespace', 'default')
    data = []
    k8s.load_auth_config(auth_type, token)

    apps_api = client.AppsV1Api()

    if request.method == 'DELETE':
        # 删除
        request_data = QueryDict(request.body)
        name = request_data.get('name')
        try:
            apps_api.delete_namespaced_stateful_set(name=name,namespace=namespace)
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
        for sts in apps_api.list_namespaced_stateful_set(namespace=namespace).items:
            name = sts.metadata.name
            namespace = sts.metadata.namespace
            labels = sts.metadata.labels
            selector = sts.spec.selector.match_labels
            replicas = sts.spec.replicas
            ready_replicas = (0 if sts.status.ready_replicas is None else sts.status.ready_replicas)
            containers = {}
            for c in sts.spec.template.spec.containers:
                containers[c.name] = c.image
            create_time = sts.metadata.creation_timestamp + datetime.timedelta(hours=8)
            create_time = datetime.datetime.strftime(create_time ,'%Y-%m-%d %H:%M:%S')

            sts = {'name':name,'namespace':namespace,'labels':labels,
                  'replicas': '%s / %s'%(ready_replicas,replicas),
                  'selector':selector,'containers':containers,
                  'create_time':create_time}

            # 适配带条件查询, 搜索
            if search_key:
                if search_key in name:
                    data.append(sts)
            else:
                data.append(sts)
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
def statefulset(request):
    return render(request, 'workload/statefulset.html')

@k8s.self_login_required
def pod_api(request):
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
            core_api.delete_namespaced_pod(name=name,namespace=namespace)
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
        for pod in core_api.list_namespaced_pod(namespace=namespace).items:
            # print(pod)
            name = pod.metadata.name
            namespace = pod.metadata.namespace
            labels = pod.metadata.labels
            pod_ip = pod.status.pod_ip
            node_name = pod.spec.node_name

            containers = []
            status = pod.status.phase
            if not pod.status.container_statuses:
                status = pod.status.conditions[-1].reason
            else:
                for c in pod.status.container_statuses:
                    c_name = c.name
                    c_image = c.image
                    restart_count = c.restart_count
                    c_status = "None"
                    if c.ready:
                        c_status = "Running"
                    else:
                        if c.state.waiting:
                            c_status = c.state.waiting.reason
                        elif c.state.terminated:
                            c_status = c.state.terminated.reason
                        elif c.last_state.terminated:
                            c_status = c.last_state.terminated.reason

                    c = {'c_name': c_name, 'c_image': c_image,
                         'restart_count': restart_count,
                         'c_status': c_status}
                    containers.append(c)

            create_time = pod.metadata.creation_timestamp + datetime.timedelta(hours=8)
            create_time = datetime.datetime.strftime(create_time, '%Y-%m-%d %H:%M:%S')

            pod = {'name':name,'namespace':namespace,'labels':labels,
                   'pod_ip':pod_ip,'containers':containers,'status':status,
                  'node_name':node_name,'create_time':create_time}

            # 适配带条件查询, 搜索
            if search_key:
                if search_key in name:
                    data.append(pod)
            else:
                data.append(pod)
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
def pod(request):
    return render(request, 'workload/pod.html')

@k8s.self_login_required
def pod_log(request):
    auth_type = request.session.get('auth_type')
    token = request.session.get('token')

    namespace = request.GET.get('namespace', None)
    name = request.GET.get('name', None)

    k8s.load_auth_config(auth_type, token)

    core_api = client.CoreV1Api()

    try:
        log_text = core_api.read_namespaced_pod_log(name=name, namespace=namespace, tail_lines=500)
        if log_text:
            code = 0
            msg = "获取日志成功!"
        elif len(log_text) == 0:
            code = 0
            msg = '没有日志'
            log_text = '没有日志!'
    except Exception as e:
        status = getattr(e, 'status')
        if status == 403:
            msg = "没有访问权限!"
        else:
            msg = "查询失败!"
        code = 1
        log_text = '获取日志失败!'

    res = {'code': code, 'msg': msg, 'data': log_text}
    return JsonResponse(res)

@k8s.self_login_required
@xframe_options_sameorigin
def pod_terminal(request):
    namespace = request.GET.get("namespace")
    pod_name = request.GET.get("pod_name")
    containers = request.GET.get("containers").split(',')  # 返回 nginx1,nginx2，转成一个列表方便前端处理
    auth_type = request.session.get('auth_type') # 认证类型和token，用于传递到websocket，websocket根据sessionid获取token，让websocket处理连接k8s认证用
    token = request.session.get('token')
    connect = {'namespace': namespace, 'pod_name': pod_name, 'containers': containers, 'auth_type': auth_type, 'token': token}
    return render(request, 'workload/pod_terminal.html', {'connect': connect})