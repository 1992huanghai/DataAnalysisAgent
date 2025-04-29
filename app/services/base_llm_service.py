from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union

class BaseLLMService(ABC):
    """
    大模型服务基类，定义大模型API的通用接口
    """
    
    def __init__(self, model: Optional[str] = None):
        """
        初始化大模型服务
        
        Args:
            model: 默认使用的模型名称
        """
        self.model = model
    
    @abstractmethod
    def chat_completion(self, 
                        messages: List[Dict[str, str]], 
                        model: Optional[str] = None,
                        temperature: float = 0.1,
                        max_tokens: int = 1024,
                        stream: bool = False,
                        **kwargs) -> Dict[str, Any]:
        """
        聊天补全API
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "你好"}]
            model: 模型名称，如果为None则使用实例的默认模型
            temperature: 温度参数，控制随机性，范围0-1
            max_tokens: 最大生成token数
            stream: 是否流式输出
            **kwargs: 其他参数
            
        Returns:
            API返回结果
        """
        pass
    
    