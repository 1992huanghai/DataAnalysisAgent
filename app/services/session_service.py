import os
import json
import uuid
import pandas as pd
import csv
from typing import Dict, List, Any
from datetime import datetime

class SessionService:
    """会话管理服务，负责会话数据的持久化存储和管理"""
    
    def __init__(self, data_dir: str):
        """初始化会话管理器
        
        Args:
            data_dir: 数据存储根目录
        """
        self.data_dir = data_dir
        self.sessions_dir = os.path.join(data_dir, "sessions")
        self.datasets_dir = os.path.join(data_dir, "datasets")  # 数据集存储目录
        
        # 确保目录存在
        os.makedirs(self.sessions_dir, exist_ok=True)
        os.makedirs(self.datasets_dir, exist_ok=True)
        
        # 会话元数据
        self.sessions_meta_path = os.path.join(data_dir, "sessions_meta.json")
        self.sessions_meta = self._load_sessions_meta()
        
        # 内存缓存
        self.sessions_cache = {}
        self.datasets_cache = {}  # 数据集缓存
    
    def _load_sessions_meta(self) -> Dict[str, Any]:
        """加载会话元数据"""
        if os.path.exists(self.sessions_meta_path):
            try:
                with open(self.sessions_meta_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载会话元数据失败: {str(e)}")
                return {"sessions": []}
        return {"sessions": []}
    
    def _save_sessions_meta(self):
        """保存会话元数据"""
        try:
            with open(self.sessions_meta_path, 'w', encoding='utf-8') as f:
                json.dump(self.sessions_meta, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存会话元数据失败: {str(e)}")
    
    def _get_session_path(self, session_id: str) -> str:
        """获取会话数据文件路径"""
        return os.path.join(self.sessions_dir, f"{session_id}.json")
    
    def _get_dataset_path(self, dataset_id: str) -> str:
        """获取数据集文件路径"""
        return os.path.join(self.datasets_dir, f"{dataset_id}.csv")
    
    def _load_session_data(self, session_id: str) -> Dict[str, Any]:
        """从文件加载会话数据"""
        session_path = self._get_session_path(session_id)
        if os.path.exists(session_path):
            try:
                with open(session_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载会话 {session_id} 数据失败: {str(e)}")
        return {"datasets": {}, "history": []}
    
    def _save_session_data(self, session_id: str, data: Dict[str, Any]):
        """保存会话数据到文件"""
        session_path = self._get_session_path(session_id)
        try:
            with open(session_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存会话 {session_id} 数据失败: {str(e)}")
    
    def _save_dataset_to_csv(self, dataset_id: str, data: Dict[str, List]) -> bool:
        """将数据集保存为CSV文件
        
        Args:
            dataset_id: 数据集ID
            data: 数据集数据，列表字典格式
            
        Returns:
            是否保存成功
        """
        dataset_path = self._get_dataset_path(dataset_id)
        try:
            # 将字典列表转换为DataFrame
            df = pd.DataFrame(data)
            # 保存为CSV
            df.to_csv(dataset_path, index=False, encoding='utf-8')
            return True
        except Exception as e:
            print(f"保存数据集 {dataset_id} 到CSV失败: {str(e)}")
            return False
    
    def _load_dataset_from_csv(self, dataset_id: str) -> Dict[str, List]:
        """从CSV文件加载数据集
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            数据集数据，列表字典格式
        """
        dataset_path = self._get_dataset_path(dataset_id)
        if not os.path.exists(dataset_path):
            return None
        
        try:
            # 读取CSV文件
            df = pd.read_csv(dataset_path, encoding='utf-8')
            # 转换为字典列表格式
            data = {}
            for column in df.columns:
                data[column] = df[column].tolist()
            return data
        except Exception as e:
            print(f"从CSV加载数据集 {dataset_id} 失败: {str(e)}")
            return None
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """获取会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据
        """
        # 先从缓存获取
        if session_id in self.sessions_cache:
            return self.sessions_cache[session_id]
        
        # 从文件加载
        session_data = self._load_session_data(session_id)
        self.sessions_cache[session_id] = session_data
        return session_data
    
    def create_session(self, name: str = "新会话") -> Dict[str, Any]:
        """创建新会话
        
        Args:
            name: 会话名称
            
        Returns:
            新会话信息
        """
        session_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        # 创建会话元数据
        session_meta = {
            "id": session_id,
            "name": name,
            "created_at": created_at,
            "updated_at": created_at
        }
        
        # 添加到元数据
        self.sessions_meta["sessions"].append(session_meta)
        self._save_sessions_meta()
        
        # 创建会话数据
        session_data = {"datasets": {}, "history": []}
        self._save_session_data(session_id, session_data)
        
        # 添加到缓存
        self.sessions_cache[session_id] = session_data
        
        return session_meta
    
    def rename_session(self, session_id: str, new_name: str) -> bool:
        """重命名会话
        
        Args:
            session_id: 会话ID
            new_name: 新名称
            
        Returns:
            是否成功
        """
        # 更新元数据
        for session in self.sessions_meta["sessions"]:
            if session["id"] == session_id:
                session["name"] = new_name
                session["updated_at"] = datetime.now().isoformat()
                self._save_sessions_meta()
                return True
        
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功
        """
        # 从元数据中删除
        self.sessions_meta["sessions"] = [
            session for session in self.sessions_meta["sessions"] 
            if session["id"] != session_id
        ]
        self._save_sessions_meta()
        
        # 删除会话数据文件
        session_path = self._get_session_path(session_id)
        if os.path.exists(session_path):
            try:
                os.remove(session_path)
            except Exception as e:
                print(f"删除会话文件 {session_id} 失败: {str(e)}")
        
        # 删除会话相关的数据集文件
        session_data = self.get_session(session_id)
        for dataset_id in session_data.get("datasets", {}):
            dataset_path = self._get_dataset_path(dataset_id)
            if os.path.exists(dataset_path):
                try:
                    os.remove(dataset_path)
                except Exception as e:
                    print(f"删除数据集文件 {dataset_id} 失败: {str(e)}")
        
        # 从缓存中删除
        if session_id in self.sessions_cache:
            del self.sessions_cache[session_id]
        
        return True
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """获取所有会话列表
        
        Returns:
            会话列表
        """
        return self.sessions_meta["sessions"]
    
    def add_dataset(self, session_id: str, dataset_id: str, dataset: Dict[str, Any]):
        """添加数据集到会话，大型数据集分离存储为CSV
        
        Args:
            session_id: 会话ID
            dataset_id: 数据集ID
            dataset: 数据集信息
        """
        session_data = self.get_session(session_id)
        
        # 创建数据集元数据
        dataset_meta = {
            "name": dataset["name"],
            "type": dataset["type"],
            "preview": dataset["preview"]  # 保留预览数据
        }
        
        # 如果是上传的文件，保留路径引用
        if "path" in dataset:
            dataset_meta["path"] = dataset["path"]
        
        # 如果包含大型数据，分离存储为CSV
        if "data" in dataset and isinstance(dataset["data"], dict):
            # 保存数据到CSV文件
            if self._save_dataset_to_csv(dataset_id, dataset["data"]):
                # 在元数据中记录数据文件路径
                dataset_meta["data_file"] = self._get_dataset_path(dataset_id)
        
        # 将元数据添加到会话
        session_data["datasets"][dataset_id] = dataset_meta
        self.sessions_cache[session_id] = session_data
        self._save_session_data(session_id, session_data)
        
        # 更新元数据中的更新时间
        for session in self.sessions_meta["sessions"]:
            if session["id"] == session_id:
                session["updated_at"] = datetime.now().isoformat()
                self._save_sessions_meta()
                break
    
    def get_dataset_data(self, session_id: str, dataset_id: str) -> Dict[str, Any]:
        """获取完整的数据集数据
        
        Args:
            session_id: 会话ID
            dataset_id: 数据集ID
            
        Returns:
            完整的数据集数据
        """
        # 检查缓存
        cache_key = f"{session_id}_{dataset_id}"
        if cache_key in self.datasets_cache:
            return self.datasets_cache[cache_key]
        
        # 获取数据集元数据
        session_data = self.get_session(session_id)
        if dataset_id not in session_data["datasets"]:
            return None
        
        dataset_meta = session_data["datasets"][dataset_id]
        
        # 如果数据存储在CSV文件中
        if "data_file" in dataset_meta:
            data = self._load_dataset_from_csv(dataset_id)
            if data:
                # 添加到缓存
                self.datasets_cache[cache_key] = data
                return data
        
        # 如果是上传的文件，需要重新加载
        elif "path" in dataset_meta:
            try:
                from app.utils.data_loader import DataLoader
                loader = DataLoader(dataset_meta["path"])
                df = loader.load_data()
                data = {}
                for column in df.columns:
                    data[column] = df[column].tolist()
                
                # 添加到缓存
                self.datasets_cache[cache_key] = data
                return data
            except Exception as e:
                print(f"从文件加载数据集 {dataset_id} 失败: {str(e)}")
                return None
        
        return None
    
    def get_datasets(self, session_id: str) -> Dict[str, Any]:
        """获取会话的数据集
        
        Args:
            session_id: 会话ID
            
        Returns:
            数据集字典
        """
        session_data = self.get_session(session_id)
        return session_data.get("datasets", {})
    
    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话的历史记录
        
        Args:
            session_id: 会话ID
            
        Returns:
            历史记录列表
        """
        session_data = self.get_session(session_id)
        return session_data.get("history", [])
    
    def add_history(self, session_id: str, history_item: Dict[str, Any]):
        """添加历史记录到会话
        
        Args:
            session_id: 会话ID
            history_item: 历史记录项
        """
        session_data = self.get_session(session_id)
        
        # 如果历史记录中包含数据集，也需要分离存储
        if "datasets" in history_item:
            for dataset_id, dataset in list(history_item["datasets"].items()):
                if "data" in dataset:
                    # 创建数据集元数据
                    dataset_meta = {
                        "name": dataset["name"],
                        "type": dataset["type"],
                        "preview": dataset["preview"]
                    }
                    
                    # 保存数据到CSV
                    if self._save_dataset_to_csv(dataset_id, dataset["data"]):
                        dataset_meta["data_file"] = self._get_dataset_path(dataset_id)
                    
                    # 替换历史记录中的数据集
                    history_item["datasets"][dataset_id] = dataset_meta
        
        session_data["history"].append(history_item)
        self.sessions_cache[session_id] = session_data
        self._save_session_data(session_id, session_data)
        
        # 更新元数据中的更新时间
        for session in self.sessions_meta["sessions"]:
            if session["id"] == session_id:
                session["updated_at"] = datetime.now().isoformat()
                self._save_sessions_meta()
                break