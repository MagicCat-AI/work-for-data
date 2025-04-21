# -*- coding:utf-8 -*-
import hashlib
import hmac
import base64
import json
import time

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder


class AIPPT():

    def __init__(self, APPId, APISecret, Text, templateId):
        self.APPid = APPId
        self.APISecret = APISecret
        self.text = Text
        self.header = {}
        self.templateId = templateId

    # 获取签名
    def get_signature(self, ts):
        try:
            # 对app_id和时间戳进行MD5加密
            auth = self.md5(self.APPid + str(ts))
            # 使用HMAC-SHA1算法对加密后的字符串进行加密
            return self.hmac_sha1_encrypt(auth, self.APISecret)
        except Exception as e:
            print(e)
            return None

    def hmac_sha1_encrypt(self, encrypt_text, encrypt_key):
        # 使用HMAC-SHA1算法对文本进行加密，并将结果转换为Base64编码
        return base64.b64encode(
            hmac.new(encrypt_key.encode('utf-8'), encrypt_text.encode('utf-8'), hashlib.sha1).digest()).decode('utf-8')

    def md5(self, text):
        # 对文本进行MD5加密，并返回加密后的十六进制字符串
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    # 创建PPT生成任务
    def create_task(self):
        url = 'https://zwapi.xfyun.cn/api/ppt/v2/create'
        timestamp = int(time.time())
        signature = self.get_signature(timestamp)
        # body= self.getbody(self.text)

        formData = MultipartEncoder(
            fields={
                # "file": (path, open(path, 'rb'), 'text/plain'),  # 如果需要上传文件，可以将文件路径通过path 传入
                # "fileUrl":"",   #文件地址（file、fileUrl、query必填其一）
                # "fileName":"",   # 文件名(带文件名后缀；如果传file或者fileUrl，fileName必填)
                "query": self.text,
                "isCardNote": str(True),  # 是否生成PPT演讲备注, True or False
                "search": str(False),  # 是否联网搜索,True or False
                "isFigure": str(True),  # 是否自动配图, True or False
                "aiImage": "normal"
                # ai配图类型： normal、advanced （isFigure为true的话生效）； normal-普通配图，20%正文配图；advanced-高级配图，50%正文配图
            }
        )

        print(formData)

        headers = {
            "appId": self.APPid,
            "timestamp": str(timestamp),
            "signature": signature,
            "Content-Type": formData.content_type
        }
        self.header = headers
        print(headers)
        response = requests.request(method="POST", url=url, data=formData, headers=headers).text
        print("生成PPT返回结果：", response)
        resp = json.loads(response)
        if (0 == resp['code']):
            return resp['data']['sid']
        else:
            print('创建PPT任务失败')
            return None

    # 构建请求body体
    def getbody(self, text):
        body = {
            "query": text,
            "templateId": self.templateId  # 模板ID举例，具体使用 /template/list 查询
        }
        return body

    # 轮询任务进度，返回完整响应信息
    def get_process(self, sid):
        # print("sid:" + sid)
        if (None != sid):
            response = requests.request("GET", url=f"https://zwapi.xfyun.cn/api/ppt/v2/progress?sid={sid}",
                                        headers=self.header).text
            print(response)
            return response
        else:
            return None

    # 获取PPT，以下载连接形式返回
    def get_result(self, task_id):

        # 创建PPT生成任务
        # task_id = self.create_task()
        # PPTurl = ''
        # 轮询任务进度
        while (True):
            response = self.get_process(task_id)
            resp = json.loads(response)
            pptStatus = resp['data']['pptStatus']
            aiImageStatus = resp['data']['aiImageStatus']
            cardNoteStatus = resp['data']['cardNoteStatus']

            if ('done' == pptStatus and 'done' == aiImageStatus and 'done' == cardNoteStatus):
                PPTurl = resp['data']['pptUrl']
                break
            else:
                time.sleep(3)
        return PPTurl

    def getHeaders(self):
        timestamp = int(time.time())
        signature = self.get_signature(timestamp)
        # body = self.getbody(self.text)

        headers = {
            "appId": self.APPid,
            "timestamp": str(timestamp),
            "signature": signature,
            "Content-Type": "application/json; charset=utf-8"
        }
        return headers

    def getTheme(self):
        url = "https://zwapi.xfyun.cn/api/ppt/v2/template/list"
        self.header = self.getHeaders()
        body = {
            "payType": "not_free",
            # "style": "简约",    # 支持按照类型查询PPT 模板
            # "color": "红色",   #  支持按照颜色查询PPT 模板
            # "industry": "教育培训",    # 支持按照颜色查询PPT 模板
            "pageNum": 2,
            "pageSize": 10
        }

        response = requests.request("GET", url=url, headers=self.header).text
        print(response)
        return response

    def createOutline(self):
        # if('' ==fileUrl and '' == filePath):
        url = "https://zwapi.xfyun.cn/api/ppt/v2/createOutline"
        body = {
            "query": self.text,
            "language": "cn",
            "search": str(False),  # 是否联网搜索,True or False
        }

        response = requests.post(url=url, json=body, headers=self.getHeaders()).text
        print("生成大纲完成：\n", response)

        return response

    def createOutlineByDoc(self, fileName, fileUrl=None, filePath=None):
        # if('' ==fileUrl and '' == filePath):
        url = "https://zwapi.xfyun.cn/api/ppt/v2/createOutlineByDoc"
        formData = MultipartEncoder(
            fields={
                "file": (filePath, open(filePath, 'rb'), 'text/plain'),  # 如果需要上传文件，可以将文件路径通过path 传入
                "fileUrl": fileUrl,  # 文件地址（file、fileUrl必填其一）
                "fileName": fileName,  # 文件名(带文件名后缀；如果传file或者fileUrl，fileName必填)
                "query": self.text,
                "language": "cn",
                "search": str(False),  # 是否联网搜索,True or False
            }
        )
        timestamp = int(time.time())
        signature = self.get_signature(timestamp)
        headers = {
            "appId": self.APPid,
            "timestamp": str(timestamp),
            "signature": signature,
            "Content-Type": formData.content_type
        }
        self.header = headers
        response = requests.post(url=url, data=formData, headers=headers).text
        print("生成大纲完成：\n", response)

        return response

    def createPptByOutline(self, outline):
        url = "https://zwapi.xfyun.cn/api/ppt/v2/createPptByOutline"
        body = {
            "query": self.text,
            "outline": outline,
            "templateId": self.templateId,  # 模板的ID,从PPT主题列表查询中获取
            "author": "XXXX",  # PPT作者名：用户自行选择是否设置作者名
            "isCardNote": True,  # 是否生成PPT演讲备注, True or False
            "search": False,  # 是否联网搜索,True or False
            "isFigure": True,  # 是否自动配图, True or False
            "aiImage": "normal",
            # ai配图类型： normal、advanced （isFigure为true的话生效）； normal-普通配图，20%正文配图；advanced-高级配图，50%正文配图

        }
        print(body)

        response = requests.post(url, json=body, headers=self.getHeaders()).text
        print("创建生成任务成功：\n", response)
        resp = json.loads(response)
        if (0 == resp['code']):
            return resp['data']['sid']
        else:
            print('创建PPT任务失败')
            return None

def PPTapi(Text):
    APPId = "b6aa1eb8"
    APISecret = "NjcyN2JiYmNjYTM3MWRlN2RlNTNkNmNh"
    templateId = ''
    Text = Text
    demo = AIPPT(APPId, APISecret, Text, templateId)
    taskid = demo.create_task()
    result = demo.get_result(taskid)
    return result






