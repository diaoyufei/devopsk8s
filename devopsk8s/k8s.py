from kubernetes import client, config
from django.shortcuts import redirect
import os

def auth_check(auth_type, str):
    if auth_type == "token":
        token = str
        configuration = client.Configuration()
        configuration.host = "https://192.168.80.64:6443"
        configuration.ssl_ca_cert = r"E:\devopsk8s\ca.crt"
        configuration.verify_ssl = True
        configuration.api_key = {"authorization": "Bearer " + token}
        client.Configuration.set_default(configuration)
        try:
            core_api = client.CoreApi()
            core_api.get_api_versions()         ## check result
            return True
        except Exception:
            return False
    elif auth_type == "kubeconfig":
        random_str = str
        file_path = os.path.join('kubeconfig', random_str)
        config.load_kube_config(r"%s" % file_path)
        try:
            core_api = client.CoreApi()
            core_api.get_api_versions()
            return True
        except Exception:
            return False

def self_login_required(func):
    def inner(request, *args, **kwargs):
        is_login = request.session.get('is_login', False)
        if is_login:
            return func(request, *args, **kwargs)
        else:
            return redirect("/login")
    return inner

# auth
def load_auth_config(auth_type, str):
    if auth_type == "token":
        token = str
        configuration = client.Configuration()
        configuration.host = "https://192.168.80.64:6443"
        configuration.ssl_ca_cert = r"%s" %(os.path.join('kubeconfig', "ca.crt"))
        configuration.verify_ssl = True
        configuration.api_key = {"authorization": "Bearer " + token}
        client.Configuration.set_default(configuration)
    elif auth_type == "kubeconfig":
        random_str = str
        file_path = os.path.join('kubeconfig', random_str)
        config.load_kube_config(r"%s" % file_path)