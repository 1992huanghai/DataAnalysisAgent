import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import threading

class ConfigService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.base_path = Path(__file__).parent.parent.parent
        self.config_path = self.base_path / 'config' / 'config.json'
        self.agents_path = self.base_path / 'config' / 'agents.json'
        
        # 存储配置文件的最后修改时间
        self.config_last_modified = 0
        self.agents_last_modified = 0
        
        # 存储配置内容
        self.config = {}
        self.agents_config = {}
        
        # 加载初始配置
        self._load_all_configs()
        
        # 启动配置监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_config_changes, daemon=True)
        self.monitor_thread.start()
        
        self._initialized = True
    
    def _load_all_configs(self):
        """加载所有配置文件"""
        self.config = self._load_config()
        self.agents_config = self._load_agents_config()
        
        # 更新文件修改时间
        if self.config_path.exists():
            self.config_last_modified = self.config_path.stat().st_mtime
        if self.agents_path.exists():
            self.agents_last_modified = self.agents_path.stat().st_mtime
    
    def _load_config(self):
        """加载全局配置文件"""
        if not self.config_path.exists():
            # 创建默认配置
            default_config = {
                "llm": {
                    "service_type": "silicon_flow",
                    "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
                },
                "data": {
                    "max_upload_size_mb": 10,
                    "allowed_extensions": [".csv", ".xlsx", ".xls"]
                },
                "ui": {
                    "theme": "light",
                    "language": "zh-CN"
                }
            }
            self.config_path.parent.mkdir(exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载全局配置文件失败: {e}")
            return {}
    
    def _load_agents_config(self):
        """加载代理配置文件"""
        if not self.agents_path.exists():
            # 创建默认代理配置
            default_agents = {
                "agents": [
                    {
                        "id": "data_analysis",
                        "name": "数据分析代理",
                        "description": "执行数据分析任务，生成分析结果",
                        "enabled": True,
                        "config": {
                            "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
                            "service_type": "silicon_flow"
                        }
                    },
                    {
                        "id": "data_visualization",
                        "name": "数据可视化代理",
                        "description": "生成数据可视化图表，创建可视化HTML页面",
                        "enabled": True,
                        "config": {
                            "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
                            "service_type": "silicon_flow"
                        }
                    }
                ]
            }
            self.agents_path.parent.mkdir(exist_ok=True)
            with open(self.agents_path, 'w', encoding='utf-8') as f:
                json.dump(default_agents, f, indent=2, ensure_ascii=False)
            return default_agents
        
        try:
            with open(self.agents_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载代理配置文件失败: {e}")
            return {"agents": []}
    
    def _monitor_config_changes(self):
        """监控配置文件变化的线程函数"""
        while True:
            try:
                # 检查全局配置文件是否变化
                if self.config_path.exists():
                    current_mtime = self.config_path.stat().st_mtime
                    if current_mtime > self.config_last_modified:
                        print("检测到全局配置文件变化，重新加载...")
                        self.config = self._load_config()
                        self.config_last_modified = current_mtime
                        self._apply_config()
                
                # 检查代理配置文件是否变化
                if self.agents_path.exists():
                    current_mtime = self.agents_path.stat().st_mtime
                    if current_mtime > self.agents_last_modified:
                        print("检测到代理配置文件变化，重新加载...")
                        self.agents_config = self._load_agents_config()
                        self.agents_last_modified = current_mtime
                
                # 每秒检查一次
                time.sleep(1)
            except Exception as e:
                print(f"监控配置文件变化时出错: {e}")
                time.sleep(5)  # 出错后等待时间长一些
    
    def get_global_config(self) -> Dict[str, Any]:
        """获取全局配置"""
        return self.config
    
    def get_agents_config(self) -> Dict[str, Any]:
        """获取代理配置"""
        return self.agents_config
    
    def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取特定代理的配置"""
        for agent in self.agents_config.get("agents", []):
            if agent.get("id") == agent_id:
                return agent
        return None
    
    def get_config_value(self, key_path: str, default=None) -> Any:
        """
        获取配置值，支持点号分隔的路径
        例如: get_config_value("data.max_upload_size_mb")
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
                
        return value
    
    def update_global_config(self, new_config: Dict[str, Any]) -> bool:
        """更新全局配置"""
        print(f"更新全局配置: {new_config}")
        
        # 更新内存中的配置
        self.config.update(new_config)
        
        # 保存到文件
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"全局配置已保存到: {self.config_path}")
            
            # 更新最后修改时间
            self.config_last_modified = self.config_path.stat().st_mtime
            
            # 确保配置立即生效
            self._apply_config()
            
            return True
        except Exception as e:
            print(f"保存全局配置失败: {e}")
            return False
    
    def update_agent_config(self, agent_id: str, new_config: Dict[str, Any]) -> bool:
        """更新特定代理的配置"""
        print(f"更新代理 {agent_id} 的配置: {new_config}")
        
        # 查找并更新代理配置
        found = False
        for agent in self.agents_config.get("agents", []):
            if agent.get("id") == agent_id:
                agent.update(new_config)
                found = True
                break
        
        if not found:
            print(f"未找到代理 {agent_id}")
            return False
        
        # 保存到文件
        try:
            with open(self.agents_path, 'w', encoding='utf-8') as f:
                json.dump(self.agents_config, f, indent=2, ensure_ascii=False)
            print(f"代理配置已保存到: {self.agents_path}")
            
            # 更新最后修改时间
            self.agents_last_modified = self.agents_path.stat().st_mtime
            
            return True
        except Exception as e:
            print(f"保存代理配置失败: {e}")
            return False
    
    def _apply_config(self):
        """应用配置到系统中"""
        print("正在应用新配置...")
        
        # 更新环境变量
        if 'llm' in self.config:
            if self.config['llm'].get('service_type') == 'silicon_flow':
                os.environ['SILICON_LLM_MODEL_NAME'] = self.config['llm'].get('model', '')
            elif self.config['llm'].get('service_type') == 'openai':
                os.environ['OPENAI_MODEL'] = self.config['llm'].get('model', '')
        
        print("配置已应用")