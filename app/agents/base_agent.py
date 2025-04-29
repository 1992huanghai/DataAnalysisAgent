from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import pandas as pd

from app.services.llm_service_factory import LLMServiceFactory

import os
from app.services.config_service import ConfigService

class BaseAgent(ABC):
    """基础代理类，所有专用代理都应继承自此类"""
    
    def __init__(self, agent_id: Optional[str] = None, service_type: Optional[str] = None, model: Optional[str] = None):
        # 获取配置服务实例
        self.config_service = ConfigService()
        
        # 确定代理ID
        self.agent_id = agent_id or self.__class__.__name__.lower().replace('agent', '')
        
        # 保存初始化参数
        self.init_service_type = service_type
        self.init_model = model
        
        # 初始化LLM服务
        self._update_llm_service()
    
    def _update_llm_service(self):
        """更新LLM服务实例，根据最新配置"""
        # 从配置服务获取代理配置
        agent_config = self.config_service.get_agent_config(self.agent_id)
        default_config = self.config_service.get_agent_config('default')
        
        # 配置优先级：初始化参数 > 特定代理配置 > 默认代理配置 > 全局配置
        self.service_type = self.init_service_type
        self.model = self.init_model
        
        # 如果初始化参数为None，则按优先级获取配置
        if self.service_type is None:
            if agent_config and agent_config.get('config', {}).get('service_type'):
                self.service_type = agent_config.get('config', {}).get('service_type')
            elif default_config and default_config.get('config', {}).get('service_type'):
                self.service_type = default_config.get('config', {}).get('service_type')
            else:
                self.service_type = self.config_service.get_config_value('llm.service_type')
                
        if self.model is None:
            if agent_config and agent_config.get('config', {}).get('model'):
                self.model = agent_config.get('config', {}).get('model')
            elif default_config and default_config.get('config', {}).get('model'):
                self.model = default_config.get('config', {}).get('model')
            else:
                self.model = self.config_service.get_config_value('llm.model')
        
        # 通过工厂类初始化LLM服务
        self.llm_service = LLMServiceFactory.get_service(service_type=self.service_type, model=self.model)
    
    def get_llm_service(self):
        """获取LLM服务，确保使用最新配置"""
        self._update_llm_service()
        return self.llm_service
    
    @abstractmethod
    def execute(self, df: pd.DataFrame, prompt: str) -> Any:
        """
        执行代理的主要功能
        
        Args:
            df: 输入的DataFrame数据
            prompt: 用户需求描述
            
        Returns:
            执行结果
        """
        pass
    
    def get_model_config(self):
        """获取模型配置"""
        # 每次调用时重新获取最新配置
        self._update_llm_service()
        return {"service_type": self.service_type, "model": self.model}
    
    def execute(self, inputs, prompt):
        """执行代理任务"""
        raise NotImplementedError("子类必须实现此方法")