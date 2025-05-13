# -*- coding:utf-8 -*-
import hashlib
import hmac
import base64
import json
import time
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class AIPPT:
    def __init__(self, app_id: str, api_secret: str, text: str, template_id: str = ""):
        self.app_id = app_id
        self.api_secret = api_secret
        self.text = text
        self.template_id = template_id
        self.base_url = "https://zwapi.xfyun.cn/api/ppt/v2"

    def _get_signature(self, timestamp: int) -> str:
        """生成签名"""
        auth = self._md5(self.app_id + str(timestamp))
        return self._hmac_sha1_encrypt(auth, self.api_secret)

    def _hmac_sha1_encrypt(self, encrypt_text: str, encrypt_key: str) -> str:
        """使用HMAC-SHA1算法加密"""
        return base64.b64encode(
            hmac.new(encrypt_key.encode('utf-8'), encrypt_text.encode('utf-8'), hashlib.sha1).digest()
        ).decode('utf-8')

    def _md5(self, text: str) -> str:
        """MD5加密"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _get_headers(self, content_type: str = "application/json; charset=utf-8") -> dict:
        """生成请求头"""
        timestamp = int(time.time())
        signature = self._get_signature(timestamp)
        return {
            "appId": self.app_id,
            "timestamp": str(timestamp),
            "signature": signature,
            "Content-Type": content_type
        }

    def create_task(self) -> str | None:
        """创建PPT生成任务"""
        url = f"{self.base_url}/create"
        headers = self._get_headers(content_type="multipart/form-data")
        form_data = MultipartEncoder(
            fields={
                "query": self.text,
                "isCardNote": "true",
                "search": "false",
                "isFigure": "true",
                "aiImage": "normal"
            }
        )
        headers["Content-Type"] = form_data.content_type
        response = requests.post(url, data=form_data, headers=headers)
        logging.info(f"生成PPT返回结果：{response.text}")
        resp = response.json()
        if resp.get("code") == 0:
            return resp.get("data", {}).get("sid")
        logging.error("创建PPT任务失败")
        return None

    def get_process(self, sid: str) -> str | None:
        """轮询任务进度"""
        if not sid:
            return None
        url = f"{self.base_url}/progress?sid={sid}"
        headers = self._get_headers()
        response = requests.get(url, headers=headers)
        logging.info(f"任务进度返回结果：{response.text}")
        return response.text

    def get_result(self, task_id: str) -> str | None:
        """获取PPT下载链接"""
        if not task_id:
            return None
        while True:
            response = self.get_process(task_id)
            if not response:
                return None
            resp = json.loads(response)
            if (
                resp.get("data", {}).get("pptStatus") == "done"
                and resp.get("data", {}).get("aiImageStatus") == "done"
                and resp.get("data", {}).get("cardNoteStatus") == "done"
            ):
                return resp.get("data", {}).get("pptUrl")
            time.sleep(3)

    def create_outline(self) -> str | None:
        """生成大纲"""
        url = f"{self.base_url}/createOutline"
        headers = self._get_headers()
        body = {
            "query": self.text,
            "language": "cn",
            "search": "false"
        }
        response = requests.post(url, json=body, headers=headers)
        logging.info(f"生成大纲返回结果：{response.text}")
        return response.text

    def create_outline_by_doc(self, file_name: str, file_url: str = None, file_path: str = None) -> str | None:
        """通过文档生成大纲"""
        url = f"{self.base_url}/createOutlineByDoc"
        headers = self._get_headers(content_type="multipart/form-data")
        fields = {
            "fileName": file_name,
            "query": self.text,
            "language": "cn",
            "search": "false"
        }
        if file_path:
            fields["file"] = (file_name, open(file_path, 'rb'), 'application/octet-stream')
        elif file_url:
            fields["fileUrl"] = file_url
        form_data = MultipartEncoder(fields=fields)
        headers["Content-Type"] = form_data.content_type
        response = requests.post(url, data=form_data, headers=headers)
        logging.info(f"通过文档生成大纲返回结果：{response.text}")
        return response.text

    def create_ppt_by_outline(self, outline: str) -> str | None:
        """通过大纲生成PPT"""
        url = f"{self.base_url}/createPptByOutline"
        headers = self._get_headers()
        body = {
            "query": self.text,
            "outline": outline,
            "templateId": self.template_id,
            "author": "XXXX",
            "isCardNote": True,
            "search": False,
            "isFigure": True,
            "aiImage": "normal"
        }
        response = requests.post(url, json=body, headers=headers)
        logging.info(f"通过大纲生成PPT返回结果：{response.text}")
        resp = response.json()
        if resp.get("code") == 0:
            return resp.get("data", {}).get("sid")
        logging.error("创建PPT任务失败")
        return None


def ppt_api(text: str) -> str | None:
    app_id = "b6aa1eb8"
    api_secret = "NjcyN2JiYmNjYTM3MWRlN2RlNTNkNmNh"
    template_id = ""
    demo = AIPPT(app_id, api_secret, text, template_id)
    task_id = demo.create_task()
    if task_id:
        return demo.get_result(task_id)
    return None