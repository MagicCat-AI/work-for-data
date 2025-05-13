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
import logging
from typing import Dict, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIException(Exception):
    """API基础异常类"""
    pass


class AuthException(APIException):
    """鉴权相关异常"""
    pass


class RequestException(APIException):
    """API请求异常"""
    pass


class ImageGenerator:
    """讯飞Spark图像生成API封装类"""

    def __init__(self, app_id: str, api_key: str, api_secret: str):
        """
        初始化图像生成器
        :param app_id: 应用ID
        :param api_key: API密钥
        :param api_secret: API密钥
        """
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.endpoint = 'http://spark-api.cn-huabei-1.xf-yun.com/v2.1/tti'

    def _generate_auth_url(self, method: str = "POST") -> str:
        """
        生成鉴权URL
        :param method: HTTP方法
        :return: 鉴权后的URL
        """
        try:
            # 解析URL
            if not self.endpoint.startswith(("http://", "https://")):
                raise AuthException("无效的端点URL格式")

            scheme_end = self.endpoint.index("://") + 3
            host_path = self.endpoint[scheme_end:]
            path_start = host_path.find("/")

            if path_start <= 0:
                raise AuthException("无效的URL路径")

            host = host_path[:path_start]
            path = host_path[path_start:]

            # 生成签名
            now = datetime.now()
            date = format_date_time(mktime(now.timetuple()))
            signature_origin = f"host: {host}\ndate: {date}\n{method} {path} HTTP/1.1"

            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                signature_origin.encode('utf-8'),
                hashlib.sha256
            ).digest()

            signature = base64.b64encode(signature).decode('utf-8')
            authorization = (
                f'api_key="{self.api_key}", algorithm="hmac-sha256", '
                f'headers="host date request-line", signature="{signature}"'
            )
            authorization = base64.b64encode(authorization.encode('utf-8')).decode('utf-8')

            return f"{self.endpoint}?{urlencode({'host': host, 'date': date, 'authorization': authorization})}"

        except Exception as e:
            raise AuthException(f"生成鉴权URL失败: {str(e)}")

    def _build_request_body(self, description: str) -> Dict:
        """
        构建请求体
        :param description: 图像描述文本
        :return: 请求体字典
        """
        return {
            "header": {
                "app_id": self.app_id,
                "uid": "123456789"  # 可改为随机生成
            },
            "parameter": {
                "chat": {
                    "domain": "general",
                    "temperature": 0.5,
                    "max_tokens": 4096
                }
            },
            "payload": {
                "message": {
                    "text": [{
                        "role": "user",
                        "content": description
                    }]
                }
            }
        }

    def _parse_response(self, response_text: str) -> str:
        """
        解析API响应
        :param response_text: API响应文本
        :return: 图像Data URL
        """
        try:
            data = json.loads(response_text)
            if data['header']['code'] != 0:
                raise RequestException(
                    f"API请求失败: {data['header']['code']}, 详情: {data}"
                )
            image_base64 = data["payload"]["choices"]["text"][0]["content"]
            return f"data:image/jpeg;base64,{image_base64}"
        except Exception as e:
            raise RequestException(f"解析响应失败: {str(e)}")

    def generate_image(self, description: str) -> Optional[str]:
        """
        生成图像
        :param description: 图像描述
        :return: 图像Data URL或None(失败时)
        """
        try:
            auth_url = self._generate_auth_url()
            request_body = self._build_request_body(description)

            logger.info("正在生成图像...")
            start_time = time.time()

            response = requests.post(
                auth_url,
                json=request_body,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            logger.info(f"请求完成，耗时{time.time() - start_time:.2f}秒")

            if response.status_code != 200:
                raise RequestException(f"API返回错误状态码: {response.status_code}")

            return self._parse_response(response.text)

        except Exception as e:
            logger.error(f"图像生成失败: {str(e)}")
            raise


if __name__ == "__main__":
    try:
        # 示例用法 - 实际使用时应从环境变量或配置文件中读取
        generator = ImageGenerator(
            app_id='b6aa1eb8',
            api_key='a2ad84a59f978fa350aa4835a42f18e1',
            api_secret='NjcyN2JiYmNjYTM3MWRlN2RlNTNkNmNh'
        )

        image_url = generator.generate_image(
            "远处有着高山，山上覆盖着冰雪，近处有着一片湛蓝的湖泊"
        )
        print("\n生成的图像链接(可直接在浏览器或HTML中使用):")
        print(image_url)

    except APIException as e:
        print(f"错误: {str(e)}")