import os
import tempfile
import importlib.util
from typing import Any, Dict, Optional, List, Union, Tuple
import json
import re
import pandas as pd
import uuid

from app.agents.base_agent import BaseAgent
from app.utils.json_utils import JSONEncoder


class DataVisualizationAgent(BaseAgent):
    """数据可视化代理，用于生成基于ECharts的可视化HTML页面"""
    
    def __init__(self, service_type: Optional[str] = None, model: Optional[str] = None):
        # 调用基类初始化，传入agent_id
        super().__init__(agent_id="data_visualization", service_type=service_type, model=model)
        
    def execute(self, inputs: List[Any], visualization_requirement: str) -> str:
        """
        执行数据可视化任务
        
        Args:
            inputs: 输入对象列表，可以是文件路径或DataFrame
            visualization_requirement: 数据可视化需求描述
            
        Returns:
            生成的HTML页面内容
        """
        # 1. 处理输入，转换为DataFrame列表
        dfs, df_names = self._process_inputs(inputs)
        
        # 2. 获取所有DataFrame的schema信息和完整数据
        schema_infos = []
        full_data = []
        
        for i, df in enumerate(dfs):
            schema_infos.append(self._get_schema_info(df))
            # 使用完整数据而非样本数据
            full_data.append(df.to_dict(orient='records'))
        
        # 3. 构建提示信息
        messages = [
            {
                "role": "system",
                "content": """你是一个数据可视化专家，可以生成基于ECharts的可视化代码。
请仅返回完整的HTML页面代码，包含必要的ECharts库引用和数据处理逻辑。
确保生成的代码能够直接在浏览器中运行，不需要额外的依赖。
请使用提供的完整数据集进行可视化，不要限制数据量。"""
            },
            {
                "role": "user",
                "content": f"""
基于以下信息生成数据可视化HTML页面：

1. 数据信息：
{json.dumps(list(zip(df_names, schema_infos)), ensure_ascii=False, indent=2,cls=JSONEncoder)}

2. 完整数据：
{json.dumps(list(zip(df_names, full_data)), ensure_ascii=False, indent=2,cls=JSONEncoder)}

3. 可视化需求：
{visualization_requirement}

请生成一个完整的HTML页面，使用ECharts库实现可视化。页面应包含：
1. 必要的HTML结构
2. ECharts库的引用
3. 数据处理逻辑
4. 图表配置和渲染代码

注意：
- 页面应该是自包含的，不需要额外的依赖
- 确保代码能够处理提供的数据格式
- 根据可视化需求选择合适的图表类型
- 添加适当的标题、图例和交互功能
- 使用提供的完整数据集，不要限制只使用部分数据
"""
            }
        ]
        
        # 4. 调用LLM生成代码
        response = self.get_llm_service().chat_completion(messages=messages)
        raw_content = response['choices'][0]['message']['content']
        
        # 5. 提取HTML代码
        html_code = self._extract_html_from_response(raw_content)
        
        # 6. 保存HTML到临时文件并返回路径
        # 不再需要注入数据，因为LLM已经使用了完整数据
        output_path = self._save_html_to_file(html_code)
        
        return output_path
    
    def _process_inputs(self, inputs: List[Any]) -> Tuple[List[pd.DataFrame], List[str]]:
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
            "row_count": len(df)
        }
        return schema_info
    
    def _get_sample_data(self, df: pd.DataFrame, sample_rows: int = 5) -> Dict[str, List]:
        """获取DataFrame的样本数据"""
        return df.head(sample_rows).to_dict(orient='list')
    
    def _extract_html_from_response(self, response_text: str) -> str:
        """从LLM响应中提取HTML代码"""
        # 尝试提取markdown格式的HTML代码块
        html_code_pattern = re.compile(r'```(?:html)?\s*([\s\S]*?)\s*```')
        matches = html_code_pattern.findall(response_text)
        
        if matches:
            return max(matches, key=len)
        
        # 如果没有找到代码块，尝试查找HTML标签
        if '<html' in response_text and '</html>' in response_text:
            start = response_text.find('<html')
            end = response_text.find('</html>') + 7
            return response_text[start:end]
        
        # 如果上述方法都失败，直接返回原始文本
        return response_text
    
    def _inject_data_to_html(self, html_code: str, dfs: List[pd.DataFrame], df_names: List[str]) -> str:
        """将DataFrame数据注入到HTML代码中"""
        # 检查HTML是否已包含数据
        if all(name in html_code for name in df_names):
            return html_code
        # 创建数据注入脚本
        data_script = "\n<script>\n"
        for i, (df, name) in enumerate(zip(dfs, df_names)):
            # 将DataFrame转换为JSON格式
            json_data = df.to_json(orient='records', date_format='iso')
            data_script += f"const {name} = {json_data};\n"
        data_script += "</script>\n"
        
        # 将数据脚本注入到HTML的head部分
        if '<head>' in html_code and '</head>' in html_code:
            head_end = html_code.find('</head>')
            html_code = html_code[:head_end] + data_script + html_code[head_end:]
        else:
            # 如果没有head标签，添加到body之前
            body_start = html_code.find('<body>')
            if body_start != -1:
                html_code = html_code[:body_start] + f"<head>{data_script}</head>\n" + html_code[body_start:]
            else:
                # 如果没有body标签，添加到html标签之后
                html_start = html_code.find('<html')
                if html_start != -1:
                    html_tag_end = html_code.find('>', html_start) + 1
                    html_code = html_code[:html_tag_end] + f"\n<head>{data_script}</head>\n" + html_code[html_tag_end:]
                else:
                    # 如果没有html标签，添加到开头
                    html_code = f"<html>\n<head>{data_script}</head>\n<body>\n{html_code}\n</body>\n</html>"
        
        return html_code
    
    def _save_html_to_file(self, html_code: str) -> str:
        """保存HTML代码到文件并返回文件路径"""
        # 创建输出目录
        output_dir = "/Users/haihuang.hh/Documents/code/interactive_data_analysis/static/visualizations"
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成唯一文件名
        file_name = f"visualization_{uuid.uuid4().hex[:8]}.html"
        file_path = os.path.join(output_dir, file_name)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_code)
        
        return file_path