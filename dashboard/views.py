from django.shortcuts import render, redirect
from django.http import JsonResponse, QueryDict
from kubernetes import client, config
import os, hashlib, random
from devopsk8s import k8s
from dashboard import node_data

# Create your views here.

@k8s.self_login_required
def index(request):
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    # echart图表: 通过ajax动态渲染/dashboard/node_resource接口获取
    # 工作负载： 访问每个资源的接口，获取count值ajax动态渲染

    # 计算资源
    n_r = node_data.node_resouces(core_api)
    # print(n_r)

    # 存储资源
    pv_list = []
    for pv in core_api.list_persistent_volume().items:
        # print(pv)
        pv_name = pv.metadata.name
        capacity = pv.spec.capacity["storage"]        # 返回字典对象
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
        create_time = pv.metadata.creation_timestamp

        data = {"pv_name": pv_name, "capacity": capacity, "access_modes": access_modes,
                "reclaim_policy": reclaim_policy, "status": status,
                "claim": claim, "storage_class": storage_class, "create_time": create_time}
        pv_list.append(data)

    return render(request, 'index.html', {"node_resource": n_r, "pv_list": pv_list})

# 仪表盘计算资源，为了方便ajax GET准备的接口
def node_resource(request):
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    res = node_data.node_resouces(core_api)
    return JsonResponse(res)

def login(request):
    if request.method == "GET":
        return render(request, 'login.html')
    elif request.method == "POST":
        print(request.POST)
        token = request.POST.get("token", None)
## token
        if token:
            if k8s.auth_check('token', token):
                request.session['is_login'] = True
                request.session['auth_type'] = 'token'
                request.session['token'] = token
                code = 0
                msg = "认证成功"
            else:
                code = 1
                msg = "Token无效"
## kubeconfig
        else:
            file_obj = request.FILES.get("file")
            random_str = hashlib.md5(str(random.random()).encode()).hexdigest()
            file_path = os.path.join('kubeconfig', random_str)
            try:
                with open(file_path, 'w', encoding='utf8') as f:
                    data = file_obj.read().decode()
                    f.write(data)
            except Exception:
                code = 1
                msg = "文件类型错误!"
            if k8s.auth_check('kubeconfig', random_str):
                request.session['is_login'] = 'True'
                request.session['auth_type'] = 'kubeconfig'
                request.session['token'] = random_str
                code = 0
                msg = "认证成功"
            else:
                code = 1
                msg = "认证文件无效!"
        res = {'code': code, 'msg': msg}
        return JsonResponse(res)

def logout(request):
    request.session.flush()
    return redirect(login)

def namespace_api(request):
    # 命名空间选择和命名空间表格使用
    code = 0
    msg = ""
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()
    if request.method == "GET":
        search_key = request.GET.get("search_key")
        data = []
        try:
            for ns in core_api.list_namespace().items:
                # print(ns.metadata.name)
                # print(ns)
                name = ns.metadata.name
                labels = ns.metadata.labels
                create_time = ns.metadata.creation_timestamp
                namespace = {'name':name, 'labels':labels, 'create_time':create_time}
                if search_key:
                    if search_key in name:
                        data.append(namespace)
                else:
                    data.append(namespace)
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
    elif request.method == "POST":
        name = request.POST['name']

        # 判断命名空间是否存在
        for ns in core_api.list_namespace().items:
            if name == ns.metadata.name:
                res = {'code': 1, "msg": "命名空间已经存在! "}
                return JsonResponse(res)

        body = client.V1Namespace(
            api_version="v1",
            kind="Namespace",
            metadata=client.V1ObjectMeta(
                name=name
            )
        )
        try:
            core_api.create_namespace(body=body)
            code = 0
            msg = "创建命名空间成功."
        except Exception as e:
            code = 1
            status = getattr(e, "status")
            if status == 403:
                msg = "没有访问权限!"
            else:
                msg = "创建失败!"
        res = {'code': code, 'msg': msg}
        # print(res)
        return JsonResponse(res)
    elif request.method == "DELETE":
        request_data = QueryDict(request.body)
        # print(request_data)
        name = request_data.get("name")
        try:
            core_api.delete_namespace(name)
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

def namespace(request):
    return render(request, 'k8s/namespace.html')

def export_resource_api(request):
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()
    apps_api = client.AppsV1Api()
    networking_api = client.NetworkingV1beta1Api()
    storage_api = client.StorageV1Api()

    namespace = request.GET.get('namespace', None)
    resource = request.GET.get('resource', None)
    name = request.GET.get('name', None)
    code = 0
    msg = ""
    result = ""

    import yaml, json
    # print(namespace)
    # print(resource)
    # print(name)
    if resource == "namespace":
        try:
            # bug，不要写py测试，print会二次处理影响结果，到时测试不通
            result = core_api.read_namespace(name=name, _preload_content=False).read()
            result = str(result,"utf-8")          # bytes转字符串
            result = yaml.safe_dump(json.loads(result))     # str/dict -> json -> yaml
        except Exception as e:
            code = 1
            msg = e
    elif resource == "deployment":
        try:
            result = apps_api.read_namespaced_deployment(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))      # json to yaml
            # print(result)
        except Exception as e:
            code = 1
            msg = e
    elif resource == "replicaset":
        try:
            result = apps_api.read_namespaced_replica_set(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "daemonset":
        try:
            result = apps_api.read_namespaced_daemon_set(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "statefulset":
        try:
            result = apps_api.read_namespaced_stateful_set(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "pod":
        try:
            result = core_api.read_namespaced_pod(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "service":
        try:
            result = core_api.read_namespaced_service(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
            # print(result)
        except Exception as e:
            code = 1
            msg = e
    elif resource == "ingress":
        try:
            result = networking_api.read_namespaced_ingress(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "pvc":
        try:
            result = core_api.read_namespaced_persistent_volume_claim(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "pv":
        try:
            result = core_api.read_persistent_volume(name=name, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "node":
        try:
            result = core_api.read_node(name=name, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "configmap":
        try:
            result = core_api.read_namespaced_config_map(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "secret":
        try:
            result = core_api.read_namespaced_secret(name=name, namespace=namespace, _preload_content=False).read()
            result = str(result, "utf-8")
            result = yaml.safe_dump(json.loads(result))
        except Exception as e:
            code = 1
            msg = e

    res = {'code': code, 'msg': msg, 'data': result}
    return JsonResponse(res)

# Refused to display 'http://127.0.0.1:8080/ace_editor' in a frame because it set 'X-Frame-Options' to 'deny'
from django.views.decorators.clickjacking import xframe_options_exempt
@xframe_options_exempt
def ace_editor(request):
    d = {}
    namespace = request.GET.get('namespace', None)
    resource = request.GET.get('resource', None)
    name = request.GET.get('name', None)
    d['namespace'] = namespace
    d['resource'] = resource
    d['name'] = name
    return render(request, 'ace_editor.html', {'data': d})