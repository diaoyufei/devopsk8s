from django.shortcuts import render,redirect
from django.http import JsonResponse, QueryDict
from kubernetes import client, config
from dashboard import node_data
import os, hashlib, random
from devopsk8s import k8s

# Create your views here.

@k8s.self_login_required
def node(request):
    return render(request, 'k8s/node.html')

@k8s.self_login_required
def node_api(request):
    # 命名空间选择和命名空间表格使用
    if request.method == "GET":
        auth_type = request.session.get("auth_type")
        token = request.session.get("token")
        k8s.load_auth_config(auth_type, token)
        core_api = client.CoreV1Api()
        search_key = request.GET.get("search_key")
        data = []
        try:
            for node in core_api.list_node_with_http_info()[0].items:
                # print(ns.metadata.name)
                # print(node)
                name = node.metadata.name
                labels = node.metadata.labels
                create_time = node.metadata.creation_timestamp
                status = node.status.conditions[-1].status
                scheduler = ("是" if node.spec.unschedulable is None else "否")
                cpu = node.status.capacity['cpu']
                memory = node.status.capacity['memory']
                kubelet_version = node.status.node_info.kubelet_version
                cri_version = node.status.node_info.container_runtime_version

                node = {"name":name, "labels":labels, "status": status,
                        "scheduler": scheduler, "cpu": cpu, "memory": memory,
                        "kubelet_version": kubelet_version, "cri_version": cri_version,
                        "create_time": create_time}
                if search_key:
                    if search_key in name:
                        data.append(node)
                else:
                    data.append(node)
                code = 0
                msg = "get data success"
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "no right"
            else:
                msg = "get data failed"
        count = len(data)

        if request.GET.get('page'):
            page = int(request.GET.get('page',1))
            limit = int(request.GET.get('limit'))
            start = (page - 1) * limit
            end = page * limit
            data = data[start:end]

        res = {'code':code, 'msg':msg, 'count':count, 'data':data}
        return JsonResponse(res)

@k8s.self_login_required
def node_details(request):
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    node_name = request.GET.get("node_name", None)
    n_r = node_data.node_resouces(core_api, node_name)
    n_i = node_data.node_info(core_api, node_name)
    return render(request, 'k8s/node_details.html', {"node_name": node_name, "node_resouces": n_r, "node_info": n_i})

@k8s.self_login_required
def node_details_pod_list(request):
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    node_name = request.GET.get("node_name", None)

    data = []
    try:
        for pod in core_api.list_pod_for_all_namespaces().items:
            # print(pod)
            name = pod.spec.node_name
            pod_name = pod.metadata.name
            namespace = pod.metadata.namespace
            status = ("运行中" if pod.status.conditions[-1].status else "异常")
            host_network = pod.spec.host_network
            pod_ip = ("主机网络" if host_network else pod.status.pod_ip)
            create_time = pod.metadata.creation_timestamp

            if name == node_name:
                if len(pod.spec.containers) == 1:
                    cpu_requests = "0"
                    cpu_limits = "0"
                    memory_requests = "0"
                    memory_limits = "0"
                    for c in pod.spec.containers:
                        cpu_requests = "0"
                        cpu_limits = "0"
                        memory_requests = "0"
                        memory_limits = "0"
                        if c.resources.requests is not None:
                            if "cpu" in c.resources.requests:
                                cpu_requests = c.resources.requests["cpu"]
                            if "memory" in c.resources.requests:
                                memory_requests = c.resources.requests["memory"]
                        if c.resources.limits is not None:
                            if "cpu" in c.resources.limits:
                                cpu_limits = c.resources.limits["cpu"]
                            if "memory" in c.resources.limits:
                                memory_limits = c.resources.limits["memory"]
                else:
                    c_r = "0"
                    c_l = "0"
                    m_r = "0"
                    m_l = "0"
                    cpu_requests = ""
                    cpu_limits = ""
                    memory_requests = ""
                    memory_limits = ""
                    for c in pod.spec.containers:
                        c_name = c.name
                        if c.resources.requests is not None:
                            if "cpu" in c.resources.requests:
                                c_r = c.resources.requests["cpu"]
                            if "memory" in c.resources.requests:
                                m_r = c.resources.requests["memory"]
                        if c.resources.limits is not None:
                            if "cpu" in c.resources.limits:
                                c_l = c.resources.limits["cpu"]
                            if "memory" in c.resources.limits:
                                m_l = c.resources.limits["memory"]

                        cpu_requests += "%s=%s<br>" %(c_name, c_r)
                        cpu_limits += "%s=%s<br>" %(c_name, c_l)
                        memory_requests += "%s=%s<br>" %(c_name, m_r)
                        memory_limits += "%s=%s<br>" %(c_name, m_l)

                pod = {"pod_name": pod_name, "namespace": namespace, "status": status, "pod_ip": pod_ip,
                       "cpu_requests": cpu_requests, "cpu_limits": cpu_limits, "memory_requests": memory_requests,
                       "memory_limits": memory_limits, "create_time": create_time}
                data.append(pod)

        page = int(request.GET.get('page',1))
        limit = int(request.GET.get('limit'))
        start = (page - 1) * limit
        end = (page) * limit
        data = data[start:end]
        count = len(data)
        code = 0
        msg = "获取数据成功"
        res = {"code": code, "msg": msg, "count": count, "data": data}
        return JsonResponse(res)
    except Exception as e:
        # print(e)
        status = getattr(e, "status")
        if status == 403:
            msg = "没有访问权限!"
        else:
            msg = "查询失败!"
        res = {"code": 1, "msg": msg}
        return JsonResponse(res)

@k8s.self_login_required
def pv(request):
    return render(request, 'k8s/pv.html')

@k8s.self_login_required
def pv_create(request):
    return render(request, 'k8s/pv_create.html')

@k8s.self_login_required
def pv_api(request):
    # 命名空间选择和命名空间表格使用
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    if request.method == "GET":
        search_key = request.GET.get("search_key")
        data = []
        try:
            for pv in core_api.list_persistent_volume().items:
                # print(pv)
                name = pv.metadata.name
                capacity = pv.spec.capacity["storage"]
                access_modes = pv.spec.access_modes
                reclaim_poliy = pv.spec.persistent_volume_reclaim_policy
                status = pv.status.phase
                if pv.spec.claim_ref is not None:
                    pvc_ns = pv.spec.claim_ref.namespace
                    pvc_name = pv.spec.claim_ref.name
                    pvc = "%s / %s" %(pvc_ns, pvc_name)
                else:
                    pvc = "未绑定"
                storage_class = pv.spec.storage_class_name
                create_time = pv.metadata.creation_timestamp
                pv = {"name": name, "capacity": capacity, "access_modes": access_modes,
                              "reclaim_policy": reclaim_poliy, "status":status, "pvc":pvc,
                              "storage_class": storage_class, "create_time": create_time}

                if search_key:
                    if search_key in name:
                        data.append(pv)
                else:
                    data.append(pv)
                code = 0
                msg = "get data success"
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "no right"
            else:
                msg = "get data failed"
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
        # return JsonResponse(123)
        name = request.POST.get("name", None)
        capacity = request.POST.get("capacity", None)
        access_mode = request.POST.get("access_mode", None)
        storage_type = request.POST.get("storage_type", None)
        server_ip = request.POST.get("server_ip", None)
        mount_path = request.POST.get("mount_path", None)
        body = client.V1PersistentVolume(
            api_version="v1",
            kind="PersistentVolume",
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1PersistentVolumeSpec(
                capacity={'storage': capacity},
                access_modes=[access_mode],
                nfs=client.V1NFSVolumeSource(
                    server=server_ip,
                    path="/ifs/kubernetes/%s" % mount_path
                )
            )
        )
        try:
            core_api.create_persistent_volume(body=body)
            code = 0
            msg = "创建成功."
        except Exception as e:
            # print(e)
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
        auth_type = request.session.get("auth_type")
        token = request.session.get("token")
        k8s.load_auth_config(auth_type, token)
        core_api = client.CoreV1Api()
        try:
            core_api.delete_persistent_volume(name)
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