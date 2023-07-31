from kubernetes import client, config
# 使用时间格式化
from devopsk8s import k8s
import re

# cpu单位转浮点数
def cpuUnitToF(str):
    if str.endswith("m"):
        n = re.findall("\d+",str)[0]
        n = round(float(n) / 1000,2)
        return n
    else:
        return float(str)

# 内存单位转GB
def memoryUnitToG(str):
    if str.endswith("M") or str.endswith("Mi"):
        m = re.findall("\d+", str)[0]
        g = round(float(m) / 1024, 2)
        return g
    elif str.endswith("K") or str.endswith("Ki"):
        k = re.findall("\d+", str)[0]
        g = round(float(k) / 1024 / 1024, 2)
        return g
    elif str.endswith("G") or str.endswith("Gi"):
        g = re.findall("\d+", str)[0]
        return float(g)

def node_info(core_api, n_name=None):
    node_info = {}
    for node in core_api.list_node().items:
        # print(node)
        node_name = node.metadata.name
        node_info[node_name] = {"node_name":"","hostname": "","internal_ip":"","os":"", "cpu_arch":"", "kernel": "","pod_cidr":"",
                                "container_runtime_version":"","kubelet_version":"","kube_proxy_version":"","labels":"","unschedulable":"","taints":"","create_time": ""}
        node_info[node_name]["node_name"] = node_name
        for i in node.status.addresses:
            if i.type == "InternalIP":
                node_info[node_name]["internal_ip"] = i.address
            elif i.type == "Hostname":
                node_info[node_name]["hostname"] = i.address
        node_info[node_name]["pod_cidr"] = node.spec.pod_cidr
        node_info[node_name]["os"] = node.status.node_info.os_image
        node_info[node_name]["kernel"] = node.status.node_info.kernel_version
        node_info[node_name]["cpu_arch"] = node.status.node_info.architecture
        node_info[node_name]["container_runtime_version"] = node.status.node_info.container_runtime_version
        node_info[node_name]["kubelet_version"] = node.status.node_info.kubelet_version
        node_info[node_name]["kube_proxy_version"] = node.status.node_info.kube_proxy_version
        # 如果node.spec.unschedulable的值是Null，返回的是否
        node_info[node_name]["unschedulable"] = ("是" if node.spec.unschedulable else "否")
        node_info[node_name]["labels"] = node.metadata.labels
        node_info[node_name]["taints"] = node.spec.taints
        node_info[node_name]["create_time"] = node.metadata.creation_timestamp

    if n_name is None:
        return node_info
    else:
        # print(node_info[n_name])
        return node_info[n_name]

def node_resouces(core_api, n_name=None):
    """
    统计node上所有容器资源分配
    最终生成字段格式:
    {"k8s-node1":{"allocatable_cpu": "","allocatable_memory":"","cpu_requests":"","cpu_limits":"","memory_requests":"","memory_limits":""},"k8s-node2": {"cpu_requests":","cpu_limits":"","memory_requests":"","memory_limits":""}}
    """
    node_resouces = {}
    for node in core_api.list_node().items:
        node_name = node.metadata.name
        node_resouces[node_name] = {"allocatable_cpu": "", "capacity_cpu":"", "allocatable_memory":"",
                                    "allocatable_ephemeral_storage":"", "capacity_ephemeral_storage":"", "capacity_pods":"", "pods_number": 0,
                                    "cpu_requests": 0, "cpu_limits": 0, "memory_requests": 0, "memory_limits": 0}
        # 可分配资源
        allocatable_cpu = node.status.allocatable['cpu']
        allocatable_memory = node.status.allocatable['memory']
        allocatable_storage = node.status.allocatable['ephemeral-storage']
        node_resouces[node_name]["allocatable_cpu"] = int(allocatable_cpu)
        node_resouces[node_name]["allocatable_memory"] = memoryUnitToG(allocatable_memory)
        node_resouces[node_name]["allocatable_ephemeral_storage"] = round(int(allocatable_storage) / 1024 / 1024 / 1024, 2)

        # 总容量
        capacity_cpu = node.status.capacity['cpu']
        capacity_memory = node.status.capacity['memory']
        capacity_storage = node.status.capacity['ephemeral-storage']
        capacity_pods = node.status.capacity['pods']
        node_resouces[node_name]["capacity_cpu"] = int(capacity_cpu)
        node_resouces[node_name]["capacity_memory"] = memoryUnitToG(capacity_memory)
        node_resouces[node_name]["capacity_ephemeral_storage"] = memoryUnitToG(capacity_storage)
        node_resouces[node_name]["capacity_pods"] = capacity_pods

        # 调度 & 准备就绪
        schdulable = node.spec.unschedulable
        # 取最新状态
        status = node.status.conditions[-1].status
        node_resouces[node_name]["schedulable"] = schdulable
        node_resouces[node_name]["status"] = status

        # 如果不传节点名称计算资源请求和资源限制并汇总，否则返回节点资源信息
        # 个人，就是说如果没有节点名，就计算所有pod的资源信息并汇总，如果有节点信息，再返回节点的信息情况。觉得不用。另这里没有发现有汇总。node_resouces[node_name]['cpu_limits']也未进行展示。
        for pod in core_api.list_pod_for_all_namespaces().items:
            pod_name = pod.metadata.name
            node_name = pod.spec.node_name
            # 如果节点名为None，说明该Pod未成功调度创建，跳出循环，不计算其中
            if node_name is None:
                continue

            # 遍历pod中容器
            for c in pod.spec.containers:
                c_name = c.name
                # 资源请求
                if c.resources.requests is not None:
                    if "cpu" in c.resources.requests:
                        cpu_request = c.resources.requests["cpu"]
                        # 之前用+=方式，但浮点数运算时会出现很多位小数，所以要用round取小数
                        node_resouces[node_name]['cpu_requests'] = round(node_resouces[node_name]['cpu_requests'] + cpuUnitToF(cpu_request),2)
                    if "memory" in c.resources.requests:
                        memory_request = c.resources.requests["memory"]
                        node_resouces[node_name]['momory_requests'] = round(node_resouces[node_name]['memory_requests'] + memoryUnitToG(memory_request),2)
                # 资源限制
                if c.resources.limits is not None:
                    if "cpu" in c.resources.limits:
                        cpu_limit = c.resources.limits["cpu"]
                        node_resouces[node_name]['cpu_limits'] = round(node_resouces[node_name]['cpu_limits'] + cpuUnitToF(cpu_limit), 2)
                    if "memory" in c.resources.limits:
                        memory_limit = c.resources.limits["memory"]
                        node_resouces[node_name]['memory_limits'] = round(node_resouces[node_name]['memory_limits'] + memoryUnitToG(memory_limit),2)
            # 添加Pod数量
            node_resouces[node_name]['pods_number'] += 1
        if n_name is None:
            return node_resouces
        else:
            # print(node_resouces[n_name])
            return node_resouces[n_name]

if __name__ == "__main__":
    config.load_kube_config("upload/k8s.kubeconfig")
    # namespace,pod,service
    core_api = client.CoreV1Api()
    # print(node_pods(core_api, "k8s-node1"))
    # print(node_resouces(core_api))
    # print(node_info(core_api))



























