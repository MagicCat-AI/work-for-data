from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage
import os
from typing import List, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SparkAIClient:
    """讯飞星火大模型API客户端"""

    def __init__(self):
        """
        初始化客户端，从环境变量读取配置
        """
        self.spark_api_url = os.getenv('SPARKAI_URL', 'wss://spark-api.xf-yun.com/v1.1/chat')
        self.spark_app_id = os.getenv('SPARKAI_APP_ID')
        self.spark_api_key = os.getenv('SPARKAI_API_KEY')
        self.spark_api_secret = os.getenv('SPARKAI_API_SECRET')
        self.spark_llm_domain = os.getenv('SPARKAI_DOMAIN', 'lite')

        if not all([self.spark_app_id, self.spark_api_key, self.spark_api_secret]):
            raise ValueError("缺少必要的星火API配置参数")

        self.llm = self._initialize_llm()

    def _initialize_llm(self) -> ChatSparkLLM:
        """初始化大模型实例"""
        return ChatSparkLLM(
            spark_api_url=self.spark_api_url,
            spark_app_id=self.spark_app_id,
            spark_api_key=self.spark_api_key,
            spark_api_secret=self.spark_api_secret,
            spark_llm_domain=self.spark_llm_domain,
            streaming=False,
        )

    def _generate_response(self, messages: List[ChatMessage]) -> str:
        """生成响应"""
        try:
            handler = ChunkPrintHandler()
            result = self.llm.generate([messages], callbacks=[handler])
            response = result.generations[0][0].text
            logger.info(f"API响应: {response[:100]}...")  # 日志记录前100个字符
            return response
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}")
            raise

    def chat(self, text: str) -> str:
        """通用对话接口"""
        messages = [ChatMessage(role="user", content=text)]
        return self._generate_response(messages)

    def generate_code(self, requirements: str) -> str:
        """代码生成接口"""
        prompt = f"""请根据以下需求编写完整、可运行的代码：

        需求描述:
        {requirements}

        要求:
        1. 提供完整的代码实现
        2. 包含必要的注释
        3. 确保代码可执行
        4. 如果有多种实现方式，提供最优解"""

        messages = [ChatMessage(role="user", content=prompt)]
        return self._generate_response(messages)

    def expand_story(self, text: str, style: str = "生动") -> str:
        """故事扩写接口"""
        prompt = f"""请以{style}的风格扩写以下故事文本：

        原文:
        {text}

        要求:
        1. 保持原文风格和情节连贯性
        2. 适当增加细节描写
        3. 扩写后的内容长度增加50%-100%
        4. 保持语言流畅自然"""

        messages = [ChatMessage(role="user", content=prompt)]
        return self._generate_response(messages)


# 使用示例
if __name__ == "__main__":
    try:
        # 初始化客户端
        client = SparkAIClient()

        # 示例1: 普通对话
        response = client.chat("你好，介绍一下你自己")
        print("\n对话结果:", response)

        # 示例2: 代码生成
        code_response = client.generate_code("用Python实现快速排序")
        print("\n生成的代码:", code_response)

        # 示例3: 故事扩写
        story_response = client.expand_story("从前有座山", style="童话")
        print("\n扩写的故事:", story_response)

    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")