from typing import Dict, Optional, Type
import os

from app.services.base_llm_service import BaseLLMService
from app.services.silicon_flow_service import SiliconFlowService
from app.utils.logger import setup_logger

logger = setup_logger("llm_service_factory")

class LLMServiceFactory:
    """
    大模型服务工厂类，用于创建和管理不同的LLM服务实例
    """
    
    # 服务类型映射
    _service_classes: Dict[str, Type[BaseLLMService]] = {
        "silicon_flow": SiliconFlowService,
    }
    
    # 服务实例缓存 - 使用(service_type, model)作为键
    _service_instances: Dict[str, BaseLLMService] = {}
    
    @classmethod
    def get_service(cls, service_type: str = None, model: str = None, **kwargs) -> BaseLLMService:
        """
        获取指定类型的LLM服务实例
        
        Args:
            service_type: 服务类型，如果为None则使用环境变量中的默认设置
            model: 模型名称，如果为None则使用环境变量中的默认设置
            **kwargs: 传递给服务构造函数的参数
            
        Returns:
            LLM服务实例
        """
        # 如果未指定服务类型，则从环境变量获取
        if service_type is None:
            service_type = os.environ.get("LLM_SERVICE_TYPE", "silicon_flow")
        
        # 如果未指定模型，则从环境变量获取 - 修改为使用SILICON_LLM_MODEL_NAME
        if model is None:
            if service_type == "silicon_flow":
                model = os.environ.get("SILICON_LLM_MODEL_NAME")
            else:
                model = os.environ.get("LLM_MODEL_NAME")
        
        # 检查服务类型是否支持
        if service_type not in cls._service_classes:
            supported_types = ", ".join(cls._service_classes.keys())
            raise ValueError(f"不支持的LLM服务类型: {service_type}，支持的类型有: {supported_types}")
        
        # 创建缓存键
        cache_key = f"{service_type}_{model}"
        
        # 如果实例已存在，直接返回
        if cache_key in cls._service_instances:
            return cls._service_instances[cache_key]
        
        # 创建新实例
        logger.info(f"创建新的LLM服务实例: {service_type}，模型: {model}")
        service_class = cls._service_classes[service_type]
        
        # 将model添加到kwargs中
        if model:
            kwargs['model'] = model
            
        service_instance = service_class(**kwargs)
        
        # 缓存实例
        cls._service_instances[cache_key] = service_instance
        
        return service_instance
    
    @classmethod
    def register_service(cls, service_type: str, service_class: Type[BaseLLMService]) -> None:
        """
        注册新的LLM服务类型
        
        Args:
            service_type: 服务类型名称
            service_class: 服务类
        """
        cls._service_classes[service_type] = service_class
        logger.info(f"注册新的LLM服务类型: {service_type}")