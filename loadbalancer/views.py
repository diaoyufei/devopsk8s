from django.shortcuts import render,redirect
from django.http import JsonResponse, QueryDict
from kubernetes import client, config
import os, hashlib, random
from devopsk8s import k8s

# Create your views here.

def service(request):
    return render(request, 'loadbalancer/service.html')

def service_api(request):
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
            for svc in core_api.list_namespaced_service(namespace=namespace).items:
                # print(svc)
                name = svc.metadata.name
                namespace = svc.metadata.namespace
                labels = svc.metadata.labels
                type = svc.spec.type
                cluster_ip = svc.spec.cluster_ip
                ports = []
                for p in svc.spec.ports:           # 不是序列,不能直接返回
                    port_name = p.name
                    port = p.port
                    target_port = p.target_port
                    protocol = p.protocol
                    node_port = ""
                    if type == "NodePort":
                        node_port = " <br> NodePort: %s" % p.node_port
                    port = {'port_name': port_name, 'port': port, 'protocol': protocol, 'target_port': target_port,
                            'node_port': node_port}
                    ports.append(port)

                selector = svc.spec.selector
                create_time = svc.metadata.creation_timestamp

                # 确认是否关联pod
                endpoint = ""
                for ep in core_api.list_namespaced_endpoints(namespace=namespace).items:
                    # print(ep)
                    if ep.metadata.name == name and ep.subsets is None:
                        endpoint = "未关联"
                    else:
                        endpoint = "已关联"

                svc = {"name": name, "namespace": namespace, "type": type,
                       "cluster_ip": cluster_ip, "ports": ports, "labels": labels,
                        "selector": selector, "endpoint": endpoint, "create_time": create_time}
                if search_key:
                    if search_key in name:
                        data.append(svc)
                else:
                    data.append(svc)
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
            core_api.delete_namespaced_service(namespace=namespace, name=name)
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

def ingress(request):
    return render(request, 'loadbalancer/ingress.html')

def ingress_api(request):
    # 命名空间选择和命名空间表格使用
    if request.method == "GET":
        auth_type = request.session.get("auth_type")
        token = request.session.get("token")
        k8s.load_auth_config(auth_type, token)
        networking_api = client.NetworkingV1beta1Api()
        search_key = request.GET.get("search_key")
        namespace = request.GET.get("namespace")
        data = []
        try:
            for ing in networking_api.list_namespaced_ingress(namespace=namespace).items:
                # print(ing)
                name = ing.metadata.name
                namespace = ing.metadata.namespace
                labels = ing.metadata.labels
                service = "None"
                http_hosts = "None"
                for h in ing.spec.rules:
                    host = h.host
                    # print(host)
                    path = ("/" if h.http.paths[0].path is None else h.http.paths[0].path)
                    # print(path)
                    service_name = h.http.paths[0].backend.service_name
                    # print(service_name)
                    service_port = h.http.paths[0].backend.service_port
                    # print(service_port)
                    http_hosts = {'host': host, 'path': path, 'service_name': service_name,
                                  'service_port': service_port}

                https_hosts = "None"
                if ing.spec.tls is None:
                    https_hosts = ing.spec.tls
                else:
                    for tls in ing.spec.tls:
                        host = tls.hosts[0]
                        # print(host)
                        secret_name = tls.secret_name
                        # print(service_name)
                        https_hosts = {'host': host, 'secret_name': secret_name}

                create_time = ing.metadata.creation_timestamp

                ing = {"name": name, "namespace": namespace, "labels": labels, "http_hosts": http_hosts,
                       "https_hosts": https_hosts, "service": service, "create_time": create_time}
                if search_key:
                    if search_key in name:
                        data.append(ing)
                else:
                    data.append(ing)
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
        networking_api = client.NetworkingV1beta1Api()
        try:
            networking_api.delete_namespaced_ingress(namespace=namespace, name=name)
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