import pandas as pd
from typing import Tuple, Optional, Union, Dict, Any
import os
import json
from app.utils.json_utils import JSONEncoder

class DataLoader:
    """数据加载器，用于读取Excel或CSV文件并提供样本数据"""
    
    def __init__(self, file_path: str):
        """
        初始化数据加载器
        
        Args:
            file_path: Excel或CSV文件路径
        """
        self.file_path = file_path
        self.data = None
        self.file_extension = os.path.splitext(file_path)[1].lower()
        
    def load_data(self) -> pd.DataFrame:
        """
        加载数据文件
        
        Returns:
            加载的DataFrame
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"文件不存在: {self.file_path}")
            
        if self.file_extension == '.csv':
            self.data = pd.read_csv(self.file_path)
        elif self.file_extension in ['.xlsx', '.xls']:
            self.data = pd.read_excel(self.file_path)
        else:
            raise ValueError(f"不支持的文件格式: {self.file_extension}")
            
        # 新增空值填充逻辑
        fill_values = {
            col: 0 if pd.api.types.is_numeric_dtype(self.data[col]) else ''
            for col in self.data.columns
        }
        self.data = self.data.fillna(value=fill_values)
        
        return self.data
    
    def get_sample(self, n_rows: int = 2) -> str:
        """
        获取数据样本和数据描述
        
        Args:
            n_rows: 样本行数
            
        Returns:
            (样本数据, 数据描述文本(JSON格式))
        """
        if self.data is None:
            self.load_data()
            
        sample = self.data.head(n_rows) 
        return json.dumps(sample.to_dict(orient='list'),cls=JSONEncoder)
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        获取数据表的schema信息，只包含字段名和字段类型
        
        Returns:
            包含schema信息的字典
        """
        if self.data is None:
            self.load_data()
            
        schema_info = {
            "columns": {
                col: str(self.data[col].dtype) 
                for col in self.data.columns
            }
        }
        
        return schema_info
    
    def get_schema_json(self) -> str:
        """
        获取数据表的schema信息，以JSON字符串形式返回
        
        Returns:
            包含schema信息的JSON字符串
        """
        schema_info = self.get_schema_info()
        return json.dumps(schema_info, ensure_ascii=False, cls=JSONEncoder)
print (DataLoader("/Users/haihuang.hh/Documents/code/data_analysis_agent/data/sample.xlsx").get_schema_json())