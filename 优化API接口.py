from typing import Dict, Any
import logging
from enum import Enum

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIType(Enum):
    """API类型枚举"""
    CHAT = "chat"
    CODE_GENERATION = "code"
    STORY_WRITING = "story"


class APIResponse:
    """标准API响应类"""

    def __init__(self, success: bool, result: Any = None, error: str = None):
        """
        初始化API响应
        :param success: 是否成功
        :param result: 返回结果
        :param error: 错误信息
        """
        self.success = success
        self.result = result
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error
        }


class APIService:
    """API服务基类"""

    def __init__(self):
        self._setup()

    def _setup(self):
        """初始化设置"""
        pass

    def process(self, input_text: str) -> APIResponse:
        """处理输入并返回响应"""
        raise NotImplementedError("子类必须实现此方法")


class ChatService(APIService):
    """聊天API服务"""

    def process(self, input_text: str) -> APIResponse:
        try:
            # 这里可以添加实际的处理逻辑
            processed_result = f"处理后的聊天内容: {input_text}"
            return APIResponse(success=True, result=processed_result)
        except Exception as e:
            logger.error(f"聊天处理失败: {str(e)}")
            return APIResponse(success=False, error="聊天处理失败")


class CodeGenerationService(APIService):
    """代码生成API服务"""

    def process(self, input_text: str) -> APIResponse:
        try:
            # 这里可以添加实际的处理逻辑
            processed_result = f"生成的代码: {input_text}"
            return APIResponse(success=True, result=processed_result)
        except Exception as e:
            logger.error(f"代码生成失败: {str(e)}")
            return APIResponse(success=False, error="代码生成失败")


class StoryWritingService(APIService):
    """故事写作API服务"""

    def process(self, input_text: str) -> APIResponse:
        try:
            # 这里可以添加实际的处理逻辑
            processed_result = f"生成的故事: {input_text}"
            return APIResponse(success=True, result=processed_result)
        except Exception as e:
            logger.error(f"故事生成失败: {str(e)}")
            return APIResponse(success=False, error="故事生成失败")


class APIFactory:
    """API工厂类"""

    @staticmethod
    def create_service(api_type: APIType) -> APIService:
        """
        创建API服务实例
        :param api_type: API类型
        :return: API服务实例
        """
        services = {
            APIType.CHAT: ChatService,
            APIType.CODE_GENERATION: CodeGenerationService,
            APIType.STORY_WRITING: StoryWritingService
        }
        return services[api_type]()


# 简化接口函数
def chat_api(text: str) -> Dict[str, Any]:
    """聊天API接口"""
    service = APIFactory.create_service(APIType.CHAT)
    return service.process(text).to_dict()


def code_generation_api(text: str) -> Dict[str, Any]:
    """代码生成API接口"""
    service = APIFactory.create_service(APIType.CODE_GENERATION)
    return service.process(text).to_dict()


def story_writing_api(text: str) -> Dict[str, Any]:
    """故事写作API接口"""
    service = APIFactory.create_service(APIType.STORY_WRITING)
    return service.process(text).to_dict()


if __name__ == "__main__":
    # 测试代码
    test_text = "这是一个测试"

    print("聊天API测试:")
    print(chat_api(test_text))

    print("\n代码生成API测试:")
    print(code_generation_api(test_text))

    print("\n故事写作API测试:")
    print(story_writing_api(test_text))