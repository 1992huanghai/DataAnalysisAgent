import os
import json
from typing import Any, Dict, Optional, List, Tuple
import pandas as pd

from app.agents.base_agent import BaseAgent
from app.utils.data_loader import DataLoader

class DataAnalysisPlanAgent(BaseAgent):
    """数据分析方案生成代理，用于根据数据信息和分析需求生成专业的数据分析方案"""
    
    def __init__(self, service_type: Optional[str] = None, model: Optional[str] = None):
        # 调用基类初始化，传入agent_id
        super().__init__(agent_id="data_analysis_plan", service_type=service_type, model=model)
        
    def execute(self, inputs: List[Any], analysis_requirement: str) -> Dict[str, Any]:
        """
        生成数据分析方案
        
        Args:
            inputs: 输入对象列表，可以是文件路径或DataFrame
            analysis_requirement: 数据分析需求描述
            
        Returns:
            包含分析方案的字典
        """
        # 1. 处理输入，转换为DataFrame列表
        dfs, df_names = self._process_inputs(inputs)
        
        # 2. 获取所有DataFrame的schema信息
        schema_infos = [self._get_schema_info(df) for df in dfs]
        
        # 3. 构建提示信息
        messages = [
            {
                "role": "system",
                "content": """你是一个专业的数据分析方案设计专家，擅长根据数据特征和用户需求设计全面、专业的数据分析方案。
请根据用户提供的数据信息和分析需求，生成一个详细的数据分析方案，包括：
1. 数据理解：对数据集的基本理解和特征分析
2. 分析目标：明确用户需要解决的问题
3. 分析方法：推荐的分析方法和技术
4. 分析步骤：详细的分析步骤和流程
5. 可视化建议：推荐的可视化方式
6. 预期结果：分析可能得出的结论和见解

请确保方案专业、全面且易于理解。"""
            },
            {
                "role": "user",
                "content": f"""
请根据以下信息生成一个专业的数据分析方案：

1. 数据信息：
{json.dumps(list(zip(df_names, schema_infos)), ensure_ascii=False, indent=2)}

2. 分析需求：
{analysis_requirement}

请提供一个结构化的分析方案，包括数据理解、分析目标、分析方法、分析步骤、可视化建议和预期结果。
"""
            }
        ]
        
        # 4. 调用LLM生成分析方案
        response = self.get_llm_service().chat_completion(messages=messages)
        plan_content = response['choices'][0]['message']['content']
        
        # 5. 返回结果
        return {
            "plan": plan_content,
            "data_info": {
                "dataset_names": df_names,
                "schema_infos": schema_infos
            }
        }
    
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
            "row_count": len(df),
            "sample_data": df.head(5).to_dict(orient="records") if not df.empty else []
        }
        return schema_info