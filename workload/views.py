from django.shortcuts import render,redirect
from django.http import JsonResponse, QueryDict
from kubernetes import client, config
import os, hashlib, random
from devopsk8s import k8s

# Create your views here.

@k8s.self_login_required
def deployment(request):
    return render(request, 'workload/deployment.html')

@k8s.self_login_required
def deployment_create(request):
    return render(request, 'workload/deployment_create.html')

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
        # print(dp)
        if dp_name == dp.metadata.name:
            name = dp.metadata.name
            namespace = dp.metadata.namespace
            replicas = dp.spec.replicas
            available_replicas = (
                0 if dp.status.available_replicas is None else dp.status.available_replicas)  # ready_replicas
            labels = dp.metadata.labels
            selector = dp.spec.selector.match_labels

            # 通过deployment反查对应service
            service = []
            svc_name = None
            for svc in core_api.list_namespaced_service(namespace=namespace).items:
                # print(svc)
                if svc.spec.selector == selector:
                    # 通过该名称筛选ingress
                    svc_name = svc.metadata.name
                    type = svc.spec.type
                    cluster_ip = svc.spec.cluster_ip
                    ports = svc.spec.ports

                    data = {"type": type, "cluster_ip": cluster_ip, "ports": ports}
                    service.append(data)

            # service没有创建，ingress也就没有 ingress->service->deployment->pod
            ingress = {"rules": None, "tls": None}
            for ing in networking_api.list_namespaced_ingress(namespace=namespace).items:
                # print(ing)
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
                # 在前端处理
                resources = c.resources
                env = c.env
                ports = c.ports
                volume_mounts = c.volume_mounts
                args = c.args
                command = c.command

                container = {"name": c_name, "image": image, "liveness_probe": liveness_probe,
                             "readiness_probe": readiness_probe,
                             "resources": resources, "env": env, "ports": ports,
                             "volume_mounts": volume_mounts, "args": args, "command": command}
                containers.append(container)

                tolerations = dp.spec.template.spec.tolerations
                rolling_update = dp.spec.strategy.rolling_update
                volumes = []
                if dp.spec.template.spec.volumes is not None:
                    # 返回类似字段格式，不知道为啥不能遍历
                    for v in dp.spec.template.spec.volumes:
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
                create_time = dp.metadata.creation_timestamp

                dp_info = {"name": name, "namespace": namespace, "replicas": replicas,
                           "available_replicas": available_replicas, "labels": labels,
                           "selector": selector, "containers": containers, "rs_number": rs_number,
                           "rolling_update": rolling_update, "create_time": create_time, "volumes": volumes,
                           "tolerations": tolerations, "service": service, "ingress": ingress}
    return render(request, 'workload/deployment_details.html', {'dp_name': dp_name, 'namespace': namespace, 'dp_info': dp_info})

@k8s.self_login_required
def deployment_api(request):
    # 获取当前用户登录凭据，调用k8s api操作命名空间
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    apps_api = client.AppsV1Api()

    # 命名空间选择和命名空间表格使用
    if request.method == "GET":
        search_key = request.GET.get("search_key")
        namespace = request.GET.get("namespace")
        data = []
        try:
            for dp in apps_api.list_namespaced_deployment(namespace=namespace).items:
                # print(dp)
                name = dp.metadata.name
                namespace = dp.metadata.namespace
                replicas = dp.spec.replicas
                available_replicas = (0 if dp.status.available_replicas is None else dp.status.available_replicas)
                labels = dp.metadata.labels
                selector = dp.spec.selector.match_labels
                if len(dp.spec.template.spec.containers) > 1:
                    images = ""
                    n = 1
                    for c in dp.spec.template.spec.containers:
                        status = ("运行中" if dp.status.conditions[0].status == "True" else "异常")
                        image = c.image
                        images += "[%s]: %s / %s" %(n, image, status)
                        images += "<br>"
                        n += 1
                else:
                    status = (
                        "运行中" if dp.status.conditions[0].status == "True" else "异常")
                    image = dp.spec.template.spec.containers[0].image
                    images = "%s / %s" %(image, status)
                create_time = dp.metadata.creation_timestamp
                dp = {"name": name, "namespace": namespace, "replicas": replicas,
                             "available_replicas": available_replicas, "labels":labels, "selector":selector,
                             "images":images, "create_time": create_time}
                if search_key:
                    if search_key in name:
                        data.append(dp)
                else:
                    data.append(dp)
            code = 0
            msg = "获取数据成功"
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "没有访问权限"
            else:
                msg = "获取数据失败"
        count = len(data)

        page = int(request.GET.get('page',1))
        limit = int(request.GET.get('limit'))
        start = (page - 1) * limit
        end = page * limit
        data = data[start:end]

        res = {'code':code, 'msg':msg, 'count':count, 'data':data}
        return JsonResponse(res)

    elif request.method == "POST":
        # print(request.POST)
        name = request.POST.get("name", None)
        namespace = request.POST.get("namespace", None)
        image = request.POST.get("image", None)
        replicas = int(request.POST.get("replicas", None))
        # 处理标签
        labels = {}
        try:
            for l in request.POST.get("labels", None).split(","):
                k = l.split("=")[0]
                v = l.split("=")[1]
                labels[k] = v
        except Exception as e:
            res = {"code": 1, "msg": "标签格式错误!"}
            return JsonResponse(res)
        resources = request.POST.get("resources", None)
        health_liveness = request.POST.get("health[liveness]", None)
        health_readiness = request.POST.get("health[readiness]", None)

        if resources == "1c2g":
            resources = client.V1ResourceRequirements(limits={"cpu":"1","memory":"2Gi"},
                                                      requests={"cpu":"0.9","memory":"1.9Gi"})
        elif resources == "2c4g":
            resources = client.V1ResourceRequirements(limits={"cpu": "2", "memory": "4Gi"},
                                                      requests={"cpu": "1.9", "memory": "3.9Gi"})
        elif resources == "4c8g":
            resources = client.V1ResourceRequirements(limits={"cpu": "4", "memory": "8Gi"},
                                                      requests={"cpu": "3.9", "memory": "7.9Gi"})
        else:
            resources = client.V1ResourceRequirements(limits={"cpu": "500m", "memory": "1Gi"},
                                                      requests={"cpu": "450m", "memory": "900Mi"})

        for dp in apps_api.list_namespaced_deployment(namespace=namespace).items:
            if name == dp.metadata.name:
                res = {"code": 1, "msg": "Deployment已经存在!"}
                return JsonResponse(res)

        body = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1DeploymentSpec(
                replicas=replicas,
                selector={'matchLabels': labels},
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels=labels),
                    spec=client.V1PodSpec(
                        containers=[client.V1Container(
                            name="web",
                            image=image,
                            env=[{"name": "TEST", "value": "123"},{"name": "DEV", "value": "456"}],
                            ports=[client.V1ContainerPort(container_port=80)],
                            resources=resources,
                        )]
                    )
                ),
            )
        )
        try:
            # response = apps_api.create_namespaced_deployment(namespace=namespace, body=body)
            # print(response)
            apps_api.create_namespaced_deployment(namespace=namespace, body=body)
            code = 0
            msg = "创建成功."
        except Exception as e:
            print(e)
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "没有访问权限!"
            else:
                msg = "创建失败!"
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)

    elif request.method == "DELETE":
        request_data = QueryDict(request.body)
        # print(request_data)
        name = request_data.get("name")
        namespace = request_data.get("namespace")
        auth_type = request.session.get("auth_type")
        token = request.session.get("token")
        k8s.load_auth_config(auth_type, token)
        apps_api = client.AppsV1Api()
        try:
            apps_api.delete_namespaced_deployment(namespace=namespace, name=name)
            code = 0
            msg = "删除成功."
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "没有删除权限."
            else:
                msg = "删除失败!"
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)
    elif request.method == "PUT":
        request_data = QueryDict(request.body)
        # print(request_data)
        name = request_data.get("name")
        namespace = request_data.get("namespace")
        replicas = int(request_data.get("replicas"))
        try:
            body = apps_api.read_namespaced_deployment(name=name, namespace=namespace)
            # print(body)
            current_replicas = body.spec.replicas
            min_replicas = 0
            max_replicas = 20
            if replicas > current_replicas and replicas < max_replicas:
                # 更新对象内副本值
                body.spec.replicas = replicas
                apps_api.patch_namespaced_deployment(name=name, namespace=namespace, body=body)
                msg = "扩容成功!"
                code = 0
            elif replicas < current_replicas and replicas > min_replicas:
                body.spec.replicas = replicas
                apps_api.patch_namespaced_deployment(name=name, namespace=namespace, body=body)
                msg = "缩容成功!"
                code = 0
            elif replicas == current_replicas:
                msg = "副本数一致!"
                code = 1
            elif replicas > max_replicas:
                msg = "副本数设置过大! 请联系管理员操作。"
                code = 1
            elif replicas == min_replicas:
                msg = "副本数不能设置0!"
                code = 1
        except Exception as e:
            status = getattr(e, "status")
            if status == 403:
                msg = "你没有扩容/缩容权限!"
            else:
                msg = "扩容/缩容失败!"
            code = 1
        res = {"code": code, "msg": msg}
        return JsonResponse(res)

@k8s.self_login_required
def replicaset_api(request):
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    apps_api = client.AppsV1Api()
    apps_beta_api = client.ExtensionsV1beta1Api()

    if request.method == "GET":
        dp_name = request.GET.get("name", None)
        # print(dp_name)
        namespace = request.GET.get("namespace", None)
        data = []
        for rs in apps_api.list_namespaced_replica_set(namespace=namespace).items:
            # print(rs)
            current_dp_name = rs.metadata.owner_references[0].name
            # print(current_dp_name)
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
                      "revision": revision, 'containers': containers, "create_time": create_time}
                data.append(rs)
        # 可选, rs默认保存10条，所以不用分页
        count = len(data)
        res = {"code": 0, "msg": "", "count": count, 'data': data}
        return JsonResponse(res)
    elif request.method == "POST":
        dp_name = request.POST.get("dp_name", None)   # deployment name
        namespace = request.POST.get("namespace", None)
        reversion = request.POST.get("reversion", None)
        body = {"name": dp_name, "rollback_to": {"revision": reversion}}
        print(dp_name)
        try:
            apps_beta_api.create_namespaced_deployment_rollback(name=dp_name, namespace=namespace, body=body)
            code = 0
            msg = "回滚成功!"
        except Exception as e:
            print(e)
            status = getattr(e, "status")
            if status == 403:
                msg = "你没有回滚权限!"
            else:
                msg = "回滚失败!"
            code = 1
        res = {"code": code, "msg": msg}
        return JsonResponse(res)

@k8s.self_login_required
def daemonset(request):
    return render(request, 'workload/daemonset.html')

@k8s.self_login_required
def daemonset_api(request):
    # 命名空间选择和命名空间表格使用
    if request.method == "GET":
        auth_type = request.session.get("auth_type")
        token = request.session.get("token")
        k8s.load_auth_config(auth_type, token)
        apps_api = client.AppsV1Api()
        search_key = request.GET.get("search_key")
        namespace = request.GET.get("namespace")
        data = []
        try:
            for ds in apps_api.list_namespaced_daemon_set(namespace).items:
                # print(ds)
                name = ds.metadata.name
                namespace = ds.metadata.namespace
                desired_number = ds.status.desired_number_scheduled
                available_number = ds.status.number_available
                labels = ds.metadata.labels
                selector = ds.spec.selector.match_labels
                containers = {}
                for c in ds.spec.template.spec.containers:
                    containers[c.name] = c.image
                create_time = ds.metadata.creation_timestamp

                ds = {"name": name, "namespace": namespace, "labels": labels, "desired_number": desired_number,
                      "available_number": available_number,
                      "selector": selector, "containers": containers, "create_time": create_time}

                # 根据搜索值返回数据
                if search_key:
                    if search_key in name:
                        data.append(ds)
                else:
                    data.append(ds)
            code = 0
            msg = "获取数据成功"
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "没有访问权限"
            else:
                msg = "获取数据失败"
        count = len(data)

        page = int(request.GET.get('page',1))
        limit = int(request.GET.get('limit'))
        start = (page - 1) * limit
        end = page * limit
        data = data[start:end]

        res = {'code':code, 'msg':msg, 'count':count, 'data':data}
        return JsonResponse(res)

    elif request.method == "DELETE":
        request_data = QueryDict(request.body)
        # print(request_data)
        name = request_data.get("name")
        namespace = request_data.get("namespace")
        auth_type = request.session.get("auth_type")
        token = request.session.get("token")
        k8s.load_auth_config(auth_type, token)
        apps_api = client.AppsV1Api()
        try:
            apps_api.delete_namespaced_daemon_set(namespace=namespace, name=name)
            code = 0
            msg = "删除成功."
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "没有删除权限."
            else:
                msg = "删除失败!"
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)

@k8s.self_login_required
def statefulset(request):
    return render(request, 'workload/statefulset.html')

@k8s.self_login_required
def statefulset_api(request):
    # 命名空间选择和命名空间表格使用
    if request.method == "GET":
        auth_type = request.session.get("auth_type")
        token = request.session.get("token")
        k8s.load_auth_config(auth_type, token)
        apps_api = client.AppsV1Api()
        search_key = request.GET.get("search_key")
        namespace = request.GET.get("namespace")
        data = []
        try:
            for sts in apps_api.list_namespaced_stateful_set(namespace).items:
                # print(sts)
                name = sts.metadata.name
                namespace = sts.metadata.namespace
                labels = sts.metadata.labels
                selector = sts.spec.selector.match_labels
                replicas = sts.spec.replicas
                ready_replicas = ("0" if sts.status.ready_replicas is None else sts.status.ready_replicas)
                service_name = sts.spec.service_name
                containers = {}
                for c in sts.spec.template.spec.containers:
                    containers[c.name] = c.image
                create_time = sts.metadata.creation_timestamp

                sts = {"name": name, "namespace": namespace, "labels": labels, "replicas": replicas,
                       "ready_replicas": ready_replicas, "service_name": service_name,
                       "selector": selector, "containers": containers, "create_time": create_time}

                # 根据搜索值返回数据
                if search_key:
                    if search_key in name:
                        data.append(sts)
                else:
                    data.append(sts)
            code = 0
            msg = "获取数据成功"
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "没有访问权限"
            else:
                msg = "获取数据失败"
        count = len(data)

        page = int(request.GET.get('page',1))
        limit = int(request.GET.get('limit'))
        start = (page - 1) * limit
        end = page * limit
        data = data[start:end]

        res = {'code':code, 'msg':msg, 'count':count, 'data':data}
        return JsonResponse(res)

    elif request.method == "DELETE":
        request_data = QueryDict(request.body)
        # print(request_data)
        name = request_data.get("name")
        namespace = request_data.get("namespace")
        auth_type = request.session.get("auth_type")
        token = request.session.get("token")
        k8s.load_auth_config(auth_type, token)
        apps_api = client.AppsV1Api()
        try:
            apps_api.delete_namespaced_stateful_set(namespace=namespace, name=name)
            code = 0
            msg = "删除成功."
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "没有删除权限."
            else:
                msg = "删除失败!"
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)

@k8s.self_login_required
def pod(request):
    return render(request, 'workload/pod.html')

@k8s.self_login_required
def pod_api(request):
    # 命名空间选择和命名空间表格使用
    if request.method == "GET":
        auth_type = request.session.get("auth_type")
        token = request.session.get("token")
        k8s.load_auth_config(auth_type, token)
        core_api = client.CoreV1Api()
        search_key = request.GET.get("search_key")
        namespace = request.GET.get("namespace")
        data = []
        try:
            for po in core_api.list_namespaced_pod(namespace).items:
                # print(po)
                name = po.metadata.name
                namespace = po.metadata.namespace
                labels = po.metadata.labels
                pod_ip = po.status.pod_ip

                containers = []
                status = "None"
                if po.status.container_statuses is None:
                    status = po.status.conditions[-1].reason
                else:
                    for c in po.status.container_statuses:
                        c_name = c.name
                        c_image = c.image

                        # restart_count
                        restart_count = c.restart_count

                        # get container situation
                        c_status = "None"                              # 个人，先赋的个值
                        if c.ready is True:
                            c_status = "Running"
                        elif c.ready is False:
                            if c.state.waiting is not None:
                                c_status = c.state.waiting.reason
                            elif c.state.terminated is not None:
                                c_status = c.state.terminated.reason
                            elif c.state.last_state.terminated is not None:
                                c_status = c.last_state.terminated.reason

                        c = {'c_name': c_name, 'c_image': c_image, 'restart_count': restart_count, 'c_status': c_status}
                        containers.append(c)

                create_time = po.metadata.creation_timestamp

                po = {"name": name, "namespace": namespace, "pod_ip": pod_ip,
                      "labels": labels, "containers": containers, "status": status,
                      "create_time": create_time}

                # 根据搜索值返回数据
                if search_key:
                    if search_key in name:
                        data.append(po)
                else:
                    data.append(po)
            code = 0
            msg = "获取数据成功"
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "没有访问权限"
            else:
                msg = "获取数据失败"
        count = len(data)

        page = int(request.GET.get('page',1))
        limit = int(request.GET.get('limit'))
        start = (page - 1) * limit
        end = page * limit
        data = data[start:end]

        res = {'code':code, 'msg':msg, 'count':count, 'data':data}
        return JsonResponse(res)

    elif request.method == "DELETE":
        request_data = QueryDict(request.body)
        # print(request_data)
        name = request_data.get("name")
        namespace = request_data.get("namespace")
        auth_type = request.session.get("auth_type")
        token = request.session.get("token")
        k8s.load_auth_config(auth_type, token)
        core_api = client.CoreV1Api()
        try:
            core_api.delete_namespaced_pod(namespace=namespace, name=name)
            code = 0
            msg = "删除成功."
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "没有删除权限."
            else:
                msg = "删除失败!"
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)

@k8s.self_login_required
def pod_log(request):
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    name = request.POST.get("name", None)
    namespace = request.POST.get("namespace", None)

    # 目前没有对Pod多容器处理
    try:
        log_text = core_api.read_namespaced_pod_log(name=name, namespace=namespace, tail_lines=500)
        # print(log_text)
        if log_text:
            code = 0
            msg = "获取日志成功! "
        elif len(log_text) == 0:
            code = 0
            msg = "没有日志!"
            log_text = "没有日志!"
    except Exception as e:
        status = getattr(e, "status")
        if status == 403:
            msg = "你没有查看日志权限!"
        else:
            msg = "获取日志失败!"
        code = 1
        log_text = "获取日志失败!"
    res = {"code": code, "msg": msg, "data": log_text}
    return JsonResponse(res)

from django.views.decorators.clickjacking import xframe_options_exempt
@xframe_options_exempt
@k8s.self_login_required
def terminal(request):
    namespace = request.GET.get("namespace")
    pod_name = request.GET.get("pod_name")
    containers = request.GET.get("containers").split(',')        # 返回 nginx1 nginx2, 转换成一个列表方便前端处理
    auth_type = request.session.get('auth_type')   # 认证类型和token，用于传递到websocket, websocket根据sessioned获取token, 让websocket处理连接k8s认证用
    token = request.session.get('token')
    connect = {'namespace': namespace, 'pod_name': pod_name, 'containers': containers, 'auth_type': auth_type, 'token': token}
    return render(request, 'workload/terminal.html', {'connect': connect})