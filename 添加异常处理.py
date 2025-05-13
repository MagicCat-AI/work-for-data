from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage
import os
from typing import Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SparkAITranslator:
    """讯飞星火大模型翻译服务封装"""

    def __init__(self):
        """
        初始化翻译器，从环境变量读取配置
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

    def _translate(self, text: str, direction: str) -> Optional[str]:
        """
        执行翻译
        :param text: 待翻译文本
        :param direction: 翻译方向 (zh2en/en2zh)
        :return: 翻译结果或None
        """
        try:
            if direction == "zh2en":
                prompt = f"""请将以下中文文本准确翻译成英文，要求：
                1. 保持专业术语的正确性
                2. 保留原文风格和语气
                3. 确保语法正确
                4. 输出仅包含翻译结果，不要添加额外内容

                原文：
                {text}"""
            else:
                prompt = f"""请将以下英文文本准确翻译成中文，要求：
                1. 翻译自然流畅，符合中文表达习惯
                2. 专业术语准确
                3. 保留原文风格
                4. 输出仅包含翻译结果，不要添加额外内容

                原文：
                {text}"""

            messages = [ChatMessage(role="user", content=prompt)]
            handler = ChunkPrintHandler()
            result = self.llm.generate([messages], callbacks=[handler])
            return result.generations[0][0].text

        except Exception as e:
            logger.error(f"翻译失败: {str(e)}")
            return None

    def chinese_to_english(self, text: str) -> Optional[str]:
        """中文翻译成英文"""
        return self._translate(text, "zh2en")

    def english_to_chinese(self, text: str) -> Optional[str]:
        """英文翻译成中文"""
        return self._translate(text, "en2zh")


def translate_chinese_to_english(text: str) -> Optional[str]:
    """
    中文翻译成英文 (简化接口)
    :param text: 中文文本
    :return: 英文翻译结果或None
    """
    try:
        translator = SparkAITranslator()
        return translator.chinese_to_english(text)
    except Exception as e:
        logger.error(f"翻译服务初始化失败: {str(e)}")
        return None


def translate_english_to_chinese(text: str) -> Optional[str]:
    """
    英文翻译成中文 (简化接口)
    :param text: 英文文本
    :return: 中文翻译结果或None
    """
    try:
        translator = SparkAITranslator()
        return translator.english_to_chinese(text)
    except Exception as e:
        logger.error(f"翻译服务初始化失败: {str(e)}")
        return None


if __name__ == "__main__":
    # 示例用法
    try:
        # 中文翻译英文示例
        chinese_text = "人工智能正在改变我们的生活方式"
        english_result = translate_chinese_to_english(chinese_text)
        print(f"中文原文: {chinese_text}")
        print(f"英文翻译: {english_result}")

        # 英文翻译中文示例
        english_text = "Machine learning is a subset of artificial intelligence"
        chinese_result = translate_english_to_chinese(english_text)
        print(f"\n英文原文: {english_text}")
        print(f"中文翻译: {chinese_result}")

    except Exception as e:
        print(f"发生错误: {str(e)}")