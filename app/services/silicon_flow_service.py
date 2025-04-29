import os
import requests
from typing import Dict, List, Optional, Any, Union
import time
import json
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

from app.services.base_llm_service import BaseLLMService
from app.utils.logger import setup_logger

logger = setup_logger("silicon_flow_service")

class SiliconFlowService(BaseLLMService):
    """
    硅基流动API服务实现
    """
    
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None, model: Optional[str] = None):
        """
        初始化硅基流动API服务
        
        Args:
            api_key: API密钥，如果为None则从环境变量获取
            api_base: API基础URL，如果为None则从环境变量获取
            model: 模型名称，如果为None则从环境变量获取
        """
        self.api_key = api_key or os.environ.get("SILICON_FLOW_API_KEY")
        self.api_base = api_base or os.environ.get("SILICON_FLOW_API_BASE", "https://api.siliconflow.cn/v1")
        self.model = model or os.environ.get("SILICON_LLM_MODEL_NAME", "Qwen/QwQ-32B")
        
        if not self.api_key:
            raise ValueError("硅基流动API密钥未设置，请设置环境变量SILICON_FLOW_API_KEY或在初始化时提供")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def chat_completion(self, 
                        messages: List[Dict[str, str]], 
                        model: Optional[str] = None,
                        temperature: float = 0.1,
                        max_tokens: int = 16384,
                        stream: bool = False,
                        top_p: float = 0.1,
                        top_k: int = 50,
                        frequency_penalty: float = 0.0,
                        presence_penalty: float = 0.0,
                        stop: Optional[Union[str, List[str]]] = None,
                        **kwargs) -> Dict[str, Any]:
        """
        调用硅基流动聊天补全API
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "你好"}]
            model: 模型名称，如果为None则使用实例的默认模型
            temperature: 温度参数，控制随机性，范围0-1
            max_tokens: 最大生成token数
            stream: 是否流式输出
            top_p: 核采样参数
            top_k: 保留概率最高的k个token
            frequency_penalty: 频率惩罚参数
            presence_penalty: 存在惩罚参数
            stop: 停止生成的标记
            **kwargs: 其他参数
            
        Returns:
            API返回结果
        """
        url = f"{self.api_base}/chat/completions"
        
        # 构建请求参数，优先使用传入的model，否则使用实例的model属性
        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": stream,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
        }
        
        # 添加可选参数
        if stop:
            payload["stop"] = stop
        
        # 添加其他自定义参数
        for key, value in kwargs.items():
            payload[key] = value
        
        try:
            logger.info(f"发送请求到硅基流动API: {url}，使用模型: {payload['model']}")
            start_time = time.time()
            
            # 添加超时参数（连接10秒，读取300秒）
            response = requests.post(url, json=payload, headers=self.headers, timeout=(10, 3000))
            response.raise_for_status()
            
            end_time = time.time()
            logger.info(f"硅基流动API请求完成，耗时: {end_time - start_time:.2f}秒")
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"硅基流动API请求失败: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"错误响应: {e.response.text}")
            raise
    
