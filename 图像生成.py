# encoding: UTF-8
import time
import requests
from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
import hashlib
import base64
import hmac
from urllib.parse import urlencode
import json


class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg


class Url:
    def __init__(self, host, path, schema):
        self.host = host
        self.path = path
        self.schema = schema


def sha256base64(data):
    sha256 = hashlib.sha256()
    sha256.update(data)
    sha256 = sha256.hexdigest()
    return base64.b64encode(sha256.digest()).decode('utf-8')


def parse_url(request_url):
    stidx = request_url.index("://")
    host = request_url[stidx + 3:]
    schema = request_url[:stidx + 3]
    edidx = host.index("/")
    if edidx <= 0:
        raise AssembleHeaderException("invalid request url:" + request_url)
    path = host[edidx:]
    host = host[:edidx]
    return Url(host, path, schema)


def assemble_ws_auth_url(request_url, method="GET", api_key="", api_secret=""):
    u = parse_url(request_url)
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))
    signature_origin = f"host: {u.host}\ndate: {date}\n{method} {u.path} HTTP/1.1"
    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'), hashlib.sha256).digest()
    signature = base64.b64encode(signature_sha).decode('utf-8')
    authorization = base64.b64encode(
        f"api_key=\"{api_key}\", algorithm=\"hmac-sha256\", headers=\"host date request-line\", signature=\"{signature}\""
        .encode('utf-8')
    ).decode('utf-8')
    return f"{request_url}?{urlencode({'host': u.host, 'date': date, 'authorization': authorization})}"


def get_body(appid, text):
    return {
        "header": {"app_id": appid, "uid": "123456789"},
        "parameter": {"chat": {"domain": "general", "temperature": 0.5, "max_tokens": 4096}},
        "payload": {"message": {"text": [{"role": "user", "content": text}]}}
    }


def parse_response(response_text):
    data = json.loads(response_text)
    if data['header']['code'] != 0:
        raise Exception(f"API请求失败: {data['header']['code']}, 详情: {data}")
    image_base64 = data["payload"]["choices"]["text"][0]["content"]
    return f"data:image/jpeg;base64,{image_base64}"  # 直接返回Data URL，无需本地存储


def generate_image_url(description, appid, apikey, apisecret):
    """
    生成图像并返回可直接使用的Data URL（无需本地保存）
    :param description: 图像生成描述
    :param appid: 应用ID
    :param apikey: 接口密钥
    :param apisecret: 接口密钥
    :return: 图像的Data URL（符合RFC 2397标准）
    """
    host_url = 'http://spark-api.cn-huabei-1.xf-yun.com/v2.1/tti'
    auth_url = assemble_ws_auth_url(host_url, method='POST', api_key=apikey, api_secret=apisecret)

    start_time = time.time()
    response = requests.post(
        auth_url,
        json=get_body(appid, description),
        headers={'Content-Type': 'application/json'}
    )
    print(f"请求耗时: {time.time() - start_time:.2f}秒")

    return parse_response(response.text)


# 示例用法
if __name__ == "__main__":
    # 配置你的鉴权信息
    APP_ID = 'b6aa1eb8'
    API_KEY = 'a2ad84a59f978fa350aa4835a42f18e1'
    API_SECRET = 'NjcyN2JiYmNjYTM3MWRlN2RlNTNkNmNh'

    try:
        image_url = generate_image_url(
            "远处有着高山，山上覆盖着冰雪，近处有着一片湛蓝的湖泊",
            appid=APP_ID,
            apikey=API_KEY,
            apisecret=API_SECRET
        )
        print("生成的图像链接（可直接在浏览器或HTML中使用）:")
        print(image_url)
    except Exception as e:
        print(f"图像生成失败: {str(e)}")