# -*- coding:utf-8 -*-
import hashlib
import hmac
import base64
import json
import time
import os
import logging
from typing import Optional, Dict, Any
from requests_toolbelt.multipart.encoder import MultipartEncoder
import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIPPTGenerator:
    """讯飞AI PPT生成服务客户端"""

    BASE_URL = "https://zwapi.xfyun.cn/api/ppt/v2"

    def __init__(self, app_id: str, api_secret: str, text: str, template_id: str = ""):
        """
        初始化PPT生成器
        :param app_id: 应用ID
        :param api_secret: API密钥
        :param text: 生成PPT的文本内容
        :param template_id: PPT模板ID (可选)
        """
        self.app_id = app_id
        self.api_secret = api_secret
        self.text = text
        self.template_id = template_id
        self.headers = {}

    def _generate_signature(self, timestamp: int) -> str:
        """
        生成API请求签名
        :param timestamp: 时间戳
        :return: 签名字符串
        """
        try:
            auth = hashlib.md5(f"{self.app_id}{timestamp}".encode('utf-8')).hexdigest()
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                auth.encode('utf-8'),
                hashlib.sha1
            ).digest()
            return base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            logger.error(f"生成签名失败: {str(e)}")
            raise ValueError("签名生成失败")

    def _get_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        """
        获取请求头
        :param content_type: 内容类型
        :return: 请求头字典
        """
        timestamp = int(time.time())
        signature = self._generate_signature(timestamp)
        return {
            "appId": self.app_id,
            "timestamp": str(timestamp),
            "signature": signature,
            "Content-Type": content_type
        }

    def create_task(self) -> Optional[str]:
        """
        创建PPT生成任务
        :return: 任务ID (sid) 或 None
        """
        url = f"{self.BASE_URL}/create"
        form_data = MultipartEncoder(
            fields={
                "query": self.text,
                "isCardNote": "True",  # 生成PPT演讲备注
                "search": "False",  # 不联网搜索
                "isFigure": "True",  # 自动配图
                "aiImage": "normal"  # 普通配图
            }
        )

        self.headers = self._get_headers(form_data.content_type)

        try:
            response = requests.post(url, data=form_data, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            if data.get('code') == 0:
                logger.info("PPT任务创建成功")
                return data['data']['sid']
            else:
                logger.error(f"PPT任务创建失败: {data.get('message', '未知错误')}")
                return None

        except Exception as e:
            logger.error(f"创建任务请求失败: {str(e)}")
            raise RuntimeError("PPT任务创建失败")

    def get_task_progress(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务进度
        :param task_id: 任务ID
        :return: 进度信息字典
        """
        if not task_id:
            raise ValueError("无效的任务ID")

        url = f"{self.BASE_URL}/progress?sid={task_id}"

        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取任务进度失败: {str(e)}")
            raise RuntimeError("无法获取任务进度")

    def get_task_result(self, task_id: str, interval: int = 3, timeout: int = 300) -> Optional[str]:
        """
        获取PPT生成结果
        :param task_id: 任务ID
        :param interval: 轮询间隔(秒)
        :param timeout: 超时时间(秒)
        :return: PPT下载URL或None
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                progress = self.get_task_progress(task_id)
                data = progress.get('data', {})

                if (data.get('pptStatus') == 'done' and
                        data.get('aiImageStatus') == 'done' and
                        data.get('cardNoteStatus') == 'done'):
                    return data.get('pptUrl')

                time.sleep(interval)
            except Exception as e:
                logger.error(f"获取结果时出错: {str(e)}")
                break

        logger.warning(f"获取PPT结果超时(最长等待{timeout}秒)")
        return None

    def generate_ppt(self) -> Optional[str]:
        """
        生成PPT完整流程
        :return: PPT下载URL或None
        """
        try:
            task_id = self.create_task()
            if task_id:
                return self.get_task_result(task_id)
            return None
        except Exception as e:
            logger.error(f"PPT生成流程失败: {str(e)}")
            raise


def generate_ppt_from_text(text: str) -> Optional[str]:
    """
    从文本生成PPT (简化接口)
    :param text: 输入文本
    :return: PPT下载URL或None
    """
    try:
        # 从环境变量获取配置
        app_id = os.getenv("XF_PPT_APP_ID")
        api_secret = os.getenv("XF_PPT_API_SECRET")

        if not all([app_id, api_secret]):
            raise ValueError("缺少必要的API配置")

        generator = AIPPTGenerator(
            app_id=app_id,
            api_secret=api_secret,
            text=text
        )
        return generator.generate_ppt()

    except Exception as e:
        logger.error(f"PPT生成失败: {str(e)}")
        return None


if __name__ == "__main__":
    # 示例用法
    sample_text = "人工智能的发展历程与未来展望"

    try:
        ppt_url = generate_ppt_from_text(sample_text)
        if ppt_url:
            print(f"PPT生成成功，下载链接: {ppt_url}")
        else:
            print("PPT生成失败")
    except Exception as e:
        print(f"发生错误: {str(e)}")