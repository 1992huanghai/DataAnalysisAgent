import json
import pandas as pd
import numpy as np
from typing import Any, Dict

class JSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理pandas和numpy的特殊类型"""
    def default(self, obj):
        # 处理分组产生的元组key（需放在其他类型判断之前）
        if isinstance(obj, tuple):
            return str(obj)  # 转换为字符串格式 "(value1, value2)"
        # 处理pandas的Interval类型
        elif isinstance(obj, pd.Interval):
            return f"[{obj.left}, {obj.right})"
        # 处理pandas的Timestamp类型
        elif isinstance(obj, pd.Timestamp):
            return int(obj.timestamp() * 1000)  # 转换为毫秒时间戳
        # 新增对Period类型的处理
        elif isinstance(obj, pd.Period):
            return str(obj)  # 转换为字符串表示，如"2023Q1"
        # 处理numpy的数据类型
        elif isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif obj.isna().any().any():
            return None
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient='records')
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, 'to_json'):
            return json.loads(obj.to_json())
        return super(JSONEncoder, self).default(obj)

def dump_json(obj: Any, file_path: str, indent: int = 2, ensure_ascii: bool = False) -> None:
    """
    将对象保存为JSON文件
    
    Args:
        obj: 要保存的对象
        file_path: 文件路径
        indent: 缩进空格数，None表示不缩进
        ensure_ascii: 是否确保ASCII编码
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=ensure_ascii, indent=indent, cls=JSONEncoder)

def load_json(file_path: str) -> Dict:
    """
    从JSON文件加载对象
    
    Args:
        file_path: 文件路径
        
    Returns:
        加载的对象
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def to_json_string(obj: Any, indent: int = None, ensure_ascii: bool = False) -> str:
    """
    将对象转换为JSON字符串
    
    Args:
        obj: 要转换的对象
        indent: 缩进空格数，None表示不缩进
        ensure_ascii: 是否确保ASCII编码
        
    Returns:
        JSON字符串
    """
    return json.dumps(obj, ensure_ascii=ensure_ascii, indent=indent, cls=JSONEncoder)