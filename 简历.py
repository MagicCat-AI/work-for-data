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
from PIL import Image
from io import BytesIO

class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg

class Url:
    def __init__(this, host, path, schema):
        this.host = host
        this.path = path
        this.schema = schema
        pass

# calculate sha256 and encode to base64
def sha256base64(data):
    sha256 = hashlib.sha256()
    sha256.update(data)
    digest = base64.b64encode(sha256.digest()).decode(encoding='utf-8')
    return digest

def parse_url(requset_url):
    stidx = requset_url.index("://")
    host = requset_url[stidx + 3:]
    schema = requset_url[:stidx + 3]
    edidx = host.index("/")
    if edidx <= 0:
        raise AssembleHeaderException("invalid request url:" + requset_url)
    path = host[edidx:]
    host = host[:edidx]
    u = Url(host, path, schema)
    return u

# 生成鉴权url
def assemble_ws_auth_url(requset_url, method="GET", api_key="", api_secret=""):
    u = parse_url(requset_url)
    host = u.host
    path = u.path
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))
    # print(date)
    # date = "Thu, 12 Dec 2019 01:57:27 GMT"
    signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
    # print(signature_origin)
    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                             digestmod=hashlib.sha256).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
        api_key, "hmac-sha256", "host date request-line", signature_sha)
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    # print(authorization_origin)
    values = {
        "host": host,
        "date": date,
        "authorization": authorization
    }

    return requset_url + "?" + urlencode(values)

# 生成请求body体
def getBody(appid,text):
    body= {
    "header": {
        "app_id": appid,
        "status": 3,
    },
    "parameter": {
        "ai_resume": {
            "resData": {
                "encoding": "utf8",
                "compress": "raw",
                "format": "json"
            }
        }
    },
    "payload": {
        "reqData": {
            "encoding": "utf8",
            "compress": "raw",
            "format": "plain",
            "status": 3,
            "text":base64.b64encode(text.encode("utf-8")).decode('utf-8')
        }
    }
}
    return body

# 发起请求并返回结果
def main(text,appid,apikey,apisecret):

    host = 'https://cn-huadong-1.xf-yun.com/v1/private/s73f4add9'
    url = assemble_ws_auth_url(host,method='POST',api_key=apikey,api_secret=apisecret)
    content = getBody(appid,text)
    # print(time.time())
    response = requests.post(url,json=content,headers={'content-type': "application/json"}).text
    # print(time.time())
    return response

def 简历api(text):
    APPID = 'b6aa1eb8'
    APISecret = 'NjcyN2JiYmNjYTM3MWRlN2RlNTNkNmNh'
    APIKEY = 'a2ad84a59f978fa350aa4835a42f18e1'

    desc = text
    res = main(desc, appid=APPID, apikey=APIKEY, apisecret=APISecret)
    print(res)
    data = json.loads(res)
    code = data['header']['code']
    if (0 == code):
        text = data['payload']['resData']['text']
        resume = base64.b64decode(text)
        return resume
