import os
from typing import Any, Dict, Optional, List, Union
import json
import pandas as pd

from app.agents.base_agent import BaseAgent
from app.utils.json_utils import JSONEncoder


class DataAnalysisConclusionAgent(BaseAgent):
    """数据分析结论代理，用于生成基于数据的分析结论和见解"""
    
    def __init__(self, service_type: Optional[str] = None, model: Optional[str] = None):
        # 调用基类初始化，传入agent_id
        super().__init__(agent_id="data_analysis_conclusion", service_type=service_type, model=model)
        
    def execute(self, inputs: List[Any], analysis_requirement: str) -> Dict[str, Any]:
        """
        执行数据分析结论生成任务
        
        Args:
            inputs: 输入对象列表，可以是文件路径或DataFrame
            analysis_requirement: 数据分析需求描述
            
        Returns:
            包含分析结论的字典
        """
        # 1. 处理输入，转换为DataFrame列表
        dfs, df_names = self._process_inputs(inputs)
        
        # 2. 获取所有DataFrame的schema信息和统计摘要
        schema_infos = []
        stat_summaries = []
        sample_data = []
        
        for i, df in enumerate(dfs):
            schema_infos.append(self._get_schema_info(df))
            stat_summaries.append(self._get_statistical_summary(df))
            sample_data.append(self._get_sample_data(df))
        
        # 3. 构建提示信息
        messages = [
            {
                "role": "system",
                "content": """你是一个数据分析专家，擅长从数据中提取有价值的见解和结论。
请根据提供的数据信息、统计摘要和用户需求，生成全面且有洞察力的数据分析结论。
你的分析应该包括数据的主要特征、关键趋势、异常值、相关性以及可能的业务含义。
请确保你的结论是基于数据的，并且对用户的分析需求有针对性的回应。"""
            },
            {
                "role": "user",
                "content": f"""
请基于以下信息生成数据分析结论：

1. 数据信息：
{json.dumps(list(zip(df_names, schema_infos)), ensure_ascii=False, indent=2, cls=JSONEncoder)}

2. 统计摘要：
{json.dumps(list(zip(df_names, stat_summaries)), ensure_ascii=False, indent=2, cls=JSONEncoder)}

3. 数据样本：
{json.dumps(list(zip(df_names, dfs)), ensure_ascii=False, indent=2, cls=JSONEncoder)}

4. 分析需求：
{analysis_requirement}

请提供一个结构化的分析结论，包括但不限于：
1. 数据概览：数据集的基本特征和质量评估
2. 关键发现：主要趋势、模式和异常
3. 深入分析：变量间的关系和可能的因果关系
4. 业务洞察：数据对业务决策的启示
5. 建议：基于数据的行动建议

请确保你的分析是全面的、有深度的，并且直接回应用户的分析需求。
"""
            }
        ]
        
        # 4. 调用LLM生成分析结论
        response = self.get_llm_service().chat_completion(messages=messages)
        conclusion = response['choices'][0]['message']['content']
        
        # 5. 返回结果
        return {
            "conclusion": conclusion
        }
    
    def _process_inputs(self, inputs: List[Any]) -> tuple[List[pd.DataFrame], List[str]]:
        """处理输入对象，转换为DataFrame列表"""
        from app.utils.data_loader import DataLoader
        
        dfs = []
        df_names = []
        
        for i, input_obj in enumerate(inputs):
            if isinstance(input_obj, pd.DataFrame):
                dfs.append(input_obj)
                df_names.append(f"df_{i}")
            elif isinstance(input_obj, str):
                try:
                    data_loader = DataLoader(input_obj)
                    df = data_loader.load_data()
                    dfs.append(df)
                    
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
        """获取DataFrame的schema信息"""
        schema_info = {
            "columns": {
                col: str(df[col].dtype) 
                for col in df.columns
            },
            "row_count": len(df),
            "column_count": len(df.columns)
        }
        return schema_info
    
    def _get_statistical_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """获取DataFrame的统计摘要"""
        # 数值列的描述性统计
        numeric_stats = {}
        for col in df.select_dtypes(include=['number']).columns:
            numeric_stats[col] = {
                "mean": df[col].mean() if not df[col].isnull().all() else None,
                "median": df[col].median() if not df[col].isnull().all() else None,
                "std": df[col].std() if not df[col].isnull().all() else None,
                "min": df[col].min() if not df[col].isnull().all() else None,
                "max": df[col].max() if not df[col].isnull().all() else None,
                "null_count": df[col].isnull().sum()
            }
        
        # 分类列的描述性统计
        categorical_stats = {}
        for col in df.select_dtypes(include=['object', 'category']).columns:
            value_counts = df[col].value_counts().head(5).to_dict()  # 只取前5个最常见的值
            categorical_stats[col] = {
                "unique_count": df[col].nunique(),
                "top_values": value_counts,
                "null_count": df[col].isnull().sum()
            }
        
        # 日期列的描述性统计
        date_stats = {}
        for col in df.select_dtypes(include=['datetime']).columns:
            date_stats[col] = {
                "min": df[col].min().isoformat() if not df[col].isnull().all() else None,
                "max": df[col].max().isoformat() if not df[col].isnull().all() else None,
                "null_count": df[col].isnull().sum()
            }
        
        return {
            "numeric": numeric_stats,
            "categorical": categorical_stats,
            "date": date_stats,
            "missing_values": df.isnull().sum().sum(),
            "duplicate_rows": df.duplicated().sum()
        }
    
    def _get_sample_data(self, df: pd.DataFrame, sample_rows: int = 5) -> Dict[str, List]:
        """获取DataFrame的样本数据"""
        return df.head(sample_rows).to_dict(orient='records')