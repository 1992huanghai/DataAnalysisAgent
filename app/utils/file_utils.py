import os
import shutil
from typing import List, Optional

def ensure_dir_exists(dir_path: str) -> None:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        dir_path: 目录路径
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

def get_project_root() -> str:
    """
    获取项目根目录
    
    Returns:
        项目根目录的绝对路径
    """
    # 获取当前文件的绝对路径
    current_file = os.path.abspath(__file__)
    # 获取utils目录
    utils_dir = os.path.dirname(current_file)
    # 获取app目录
    app_dir = os.path.dirname(utils_dir)
    # 获取项目根目录
    project_root = os.path.dirname(app_dir)
    
    return project_root

def list_files(dir_path: str, extensions: Optional[List[str]] = None) -> List[str]:
    """
    列出目录中的文件
    
    Args:
        dir_path: 目录路径
        extensions: 文件扩展名列表，如果为None则列出所有文件
        
    Returns:
        文件路径列表
    """
    if not os.path.exists(dir_path):
        return []
        
    files = []
    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)
        if os.path.isfile(file_path):
            if extensions is None or any(file.lower().endswith(ext.lower()) for ext in extensions):
                files.append(file_path)
    
    return files

def safe_delete_file(file_path: str) -> bool:
    """
    安全删除文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否成功删除
    """
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return True
        except Exception:
            return False
    return False