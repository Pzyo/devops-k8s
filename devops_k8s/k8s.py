from kubernetes import client, config
import yaml
from dashboard.models import User
from django.shortcuts import redirect
from datetime import datetime, timedelta

k8s_apiserver_company = "https://192.168.64.20:6443"  # 公司环境的k8s APISERVER地址
k8s_apiserver_home = "https://192.168.10.50:6443"     # 家环境的k8s APISERVER地址

def auth_check(auth_type, token):
    if auth_type == "token":
        # 验证token是否对k8s有效
        configuration = client.Configuration()
        configuration.host = k8s_apiserver_company
        # configuration.host = k8s_apiserver_home
        # configuration.ssl_ca_cert = os.path.join(os.getcwd(), "ca.crt")
        configuration.verify_ssl = False
        configuration.api_key = {"authorization": ' '.join(("Bearer", token))}
        client.Configuration.set_default(configuration)
        try:
            core_pai = client.CoreApi()
            core_pai.get_api_versions()
            return True
        except Exception as e:
            return False
    elif auth_type == "kubeconfig":
        try:
            user_obj = User.objects.filter(token=token).first()
            content = user_obj.content
            yaml_content = yaml.load(content, Loader=yaml.FullLoader)
            config.load_kube_config_from_dict(yaml_content)
            core_pai = client.CoreApi()
            core_pai.get_api_versions()
            return True
        except Exception as e:
            print(e)
            return False

def self_login_required(func):
    """
    登录认证装饰器
    :param func:
    :return:
    """
    def inner(request, *args, **kwargs):
        is_login = request.session.get('is_login', False)
        if is_login:
            return func(request, *args, **kwargs)
        else:
            return redirect('/login')
    return inner

# 加载认证配置
def load_auth_config(auth_type, token):
    if auth_type == "token":
        # 验证token是否对k8s有效
        configuration = client.Configuration()
        configuration.host = k8s_apiserver_company
        # configuration.ssl_ca_cert = os.path.join(os.getcwd(), "ca.crt")
        configuration.verify_ssl = False
        configuration.api_key = {"authorization": ' '.join(("Bearer", token))}
        client.Configuration.set_default(configuration)
    elif auth_type == "kubeconfig":
        user_obj = User.objects.filter(token=token).first()
        content = user_obj.content
        yaml_content = yaml.load(content, Loader=yaml.FullLoader)
        config.load_kube_config_from_dict(yaml_content)

def dt_format(dt):
    current_datetime = dt + timedelta(hours=8)
    dt = datetime.strftime(current_datetime, '%Y-%m-%d %H:%M:%S')
    return dt