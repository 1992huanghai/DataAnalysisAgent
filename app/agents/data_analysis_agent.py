import os
import tempfile
import importlib.util
from typing import Any, Dict, Optional, List, Union, Tuple
import json
import re
import pandas as pd

from app.agents.base_agent import BaseAgent
from app.utils.data_loader import DataLoader

class DataAnalysisAgent(BaseAgent):
    """数据分析代理，用于生成和执行数据分析代码"""
    
    def __init__(self, service_type: Optional[str] = None, model: Optional[str] = None):
        # 调用基类初始化，传入agent_id
        super().__init__(agent_id="data_analysis", service_type=service_type, model=model)
        self.generated_code = ""  # 添加一个属性来存储生成的代码
        
    # 示例修改
    def execute(self, inputs: List[Any], analysis_requirement: str) -> Dict[str, pd.DataFrame]:
        """
        执行数据分析任务
        
        Args:
            inputs: 输入对象列表，可以是文件路径或DataFrame
            analysis_requirement: 数据分析需求描述
            
        Returns:
            包含多个分析结果DataFrame的字典，键为描述，值为DataFrame
        """
        # 1. 处理输入，转换为DataFrame列表
        dfs, df_names = self._process_inputs(inputs)
        
        # 2. 获取所有DataFrame的schema信息
        schema_infos = [self._get_schema_info(df) for df in dfs]
        
        # 3. 构建提示信息
        messages = [
            {
                "role": "system",
                "content": "你是一个数据分析专家，可以生成Python代码来分析数据。请仅返回可执行的Python代码，不要包含任何解释。注意要结合输入数据schema，和输入数据完美适配，不要有bug"
            },
            {
                "role": "user",
                "content": f"""
基于以下信息生成Python代码：

1. 数据信息：
{json.dumps(list(zip(df_names, schema_infos)), ensure_ascii=False, indent=2)}

2. 分析需求：
{analysis_requirement}

请生成一个完整的Python函数，函数名为'analyze_data'，接收一个包含多个pandas DataFrame的列表参数'dfs'，
返回一个字典，其中键为分析结果的简要描述，值为对应的DataFrame结果。

示例返回格式：
{{
    "基本统计信息": df_stats,
    "分类统计": df_category_stats,
    ...
}}
"""
            }
        ]
        
        # 4. 调用LLM生成代码
        response = self.get_llm_service().chat_completion(messages=messages)
        raw_content = response['choices'][0]['message']['content']
        
        # 使用正则表达式提取代码块
        self.generated_code = self._extract_code_from_response(raw_content)
        
        # 5. 创建临时Python模块并执行代码
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as temp_file:
            temp_file.write(self.generated_code)
            temp_module_path = temp_file.name
        
        try:
            # 导入临时模块
            spec = importlib.util.spec_from_file_location("temp_analysis", temp_module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 执行分析
            result = module.analyze_data(dfs)
            
            # 确保返回的是字典，且值都是DataFrame
            if not isinstance(result, dict):
                raise TypeError("分析函数必须返回字典类型的结果")
            final_result = {}
            for key, value in result.items():
                if not isinstance(value, pd.DataFrame):
                    raise TypeError(f"分析结果'{key}'必须是DataFrame类型")
                else:
                    final_result[key]=value.to_dict(orient='list')
            return final_result
        finally:
            # 清理临时文件
            os.unlink(temp_module_path)
    
    def _process_inputs(self, inputs: List[Any]) -> Tuple[List[pd.DataFrame], List[str]]:
        """
        处理输入对象，转换为DataFrame列表
        
        Args:
            inputs: 输入对象列表
            
        Returns:
            (DataFrame列表, DataFrame名称列表)
        """
        dfs = []
        df_names = []
        
        for i, input_obj in enumerate(inputs):
            if isinstance(input_obj, pd.DataFrame):
                # 如果输入是DataFrame，直接添加
                dfs.append(input_obj)
                df_names.append(f"df_{i}")
            elif isinstance(input_obj, str):
                # 如果输入是字符串，尝试作为文件路径加载
                try:
                    data_loader = DataLoader(input_obj)
                    df = data_loader.load_data()
                    dfs.append(df)
                    
                    # 使用文件名作为DataFrame名称
                    file_name = os.path.basename(input_obj)
                    base_name = os.path.splitext(file_name)[0]
                    df_names.append(base_name)
                except Exception as e:
                    raise ValueError(f"无法从路径加载数据: {input_obj}, 错误: {str(e)}")
            else:
                raise TypeError(f"不支持的输入类型: {type(input_obj)}")
                
        if not dfs:
            raise ValueError("没有有效的输入数据")
            
        return dfs, df_names
    
    def _get_schema_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取DataFrame的schema信息
        
        Args:
            df: 输入的DataFrame
            
        Returns:
            包含schema信息的字典
        """
        schema_info = {
            "columns": {
                col: str(df[col].dtype) 
                for col in df.columns
            },
            "row_count": len(df)
        }
        return schema_info
    
    def _extract_code_from_response(self, response_text: str) -> str:
        """
        从LLM响应中提取Python代码
        
        Args:
            response_text: LLM返回的原始文本
            
        Returns:
            提取的Python代码
        """
        # 方法1: 尝试提取markdown格式的Python代码块
        python_code_pattern = re.compile(r'```(?:python)?\s*([\s\S]*?)\s*```')
        matches = python_code_pattern.findall(response_text)
        
        if matches:
            # 如果找到了代码块，返回最长的那个（通常是完整的函数）
            return max(matches, key=len)
        
        # 方法2: 如果没有找到代码块，尝试查找函数定义
        function_pattern = re.compile(r'def\s+analyze_data\s*\(\s*dfs\s*\)[\s\S]*?(?:return|pass)')
        function_matches = function_pattern.findall(response_text)
        
        if function_matches:
            return max(function_matches, key=len)
        
        # 方法3: 如果上述方法都失败，直接返回原始文本
        return response_text