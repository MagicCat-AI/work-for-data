import requests
import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
from typing import Optional, Dict

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class API异常(Exception):
    """API基础异常类"""
    pass


class 认证异常(API异常):
    """鉴权相关异常"""
    pass


class 请求异常(API异常):
    """API请求异常"""
    pass


class 简历优化器:
    def __init__(self, 应用ID: str, API密钥: str, API密匙: str):

        self.应用ID = 应用ID
        self.API密钥 = API密钥
        self.API密匙 = API密匙
        self.接口地址 = 'https://cn-huadong-1.xf-yun.com/v1/private/s73f4add9'

    def _生成鉴权URL(self, 请求方法: str = "POST") -> str:

        try:
            # 解析接口地址
            if not self.接口地址.startswith("https://"):
                raise 认证异常("接口地址格式错误")

            主机名 = self.接口地址[8:].split("/")[0]
            路径 = "/" + "/".join(self.接口地址[8:].split("/")[1:])

            # 生成签名
            当前时间 = datetime.now()
            日期 = format_date_time(mktime(当前时间.timetuple()))
            签名原文 = f"host: {主机名}\ndate: {日期}\n{请求方法} {路径} HTTP/1.1"

            签名 = hmac.new(
                self.API密匙.encode('utf-8'),
                签名原文.encode('utf-8'),
                hashlib.sha256
            ).digest()

            签名 = base64.b64encode(签名).decode('utf-8')
            授权信息 = (
                f'api_key="{self.API密钥}", algorithm="hmac-sha256", '
                f'headers="host date request-line", signature="{签名}"'
            )
            授权信息 = base64.b64encode(授权信息.encode('utf-8')).decode('utf-8')

            # 构造URL参数
            参数 = {
                "host": 主机名,
                "date": 日期,
                "authorization": 授权信息
            }

            return f"{self.接口地址}?{urlencode(参数)}"

        except Exception as 错误:
            raise 认证异常(f"生成鉴权URL失败: {str(错误)}")

    def _构造请求体(self, 简历文本: str) -> Dict:

        return {
            "header": {
                "app_id": self.应用ID,
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
                    "text": base64.b64encode(简历文本.encode("utf-8")).decode('utf-8')
                }
            }
        }

    def 优化简历(self, 原始简历: str) -> Optional[str]:

        try:
            # 准备请求
            鉴权URL = self._生成鉴权URL()
            请求体 = self._构造请求体(原始简历)

            logger.info("正在发送简历优化请求...")
            开始时间 = time.time()

            # 发送请求
            响应 = requests.post(
                鉴权URL,
                json=请求体,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            logger.info(f"请求完成，耗时{time.time() - 开始时间:.2f}秒")

            # 处理响应
            if 响应.status_code != 200:
                raise 请求异常(f"接口返回错误状态码: {响应.status_code}")

            响应数据 = 响应.json()

            if 响应数据['header']['code'] != 0:
                raise 请求异常(f"接口返回业务错误: {响应数据['header']}")

            # 解码优化后的简历
            编码文本 = 响应数据['payload']['resData']['text']
            优化简历 = base64.b64decode(编码文本).decode('utf-8')

            return 优化简历

        except Exception as 错误:
            logger.error(f"简历优化失败: {str(错误)}")
            raise


# 使用示例
if __name__ == "__main__":
    try:
        # 实际使用时应从环境变量或配置文件中读取
        配置 = {
            "APP_ID": "你的应用ID",
            "API_KEY": "你的API密钥",
            "API_SECRET": "你的API密匙"
        }

        # 创建优化器实例
        优化器 = 简历优化器(
            应用ID=配置["APP_ID"],
            API密钥=配置["API_KEY"],
            API密匙=配置["API_SECRET"]
        )

        # 执行优化
        优化结果 = 优化器.优化简历(测试简历)
        print("\n优化后的简历：")
        print(优化结果)

    except API异常 as 错误:
        print(f"发生错误: {str(错误)}")