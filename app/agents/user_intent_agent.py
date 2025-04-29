import re
from typing import Any, Dict, Optional, List, Tuple

from app.agents.base_agent import BaseAgent

class UserIntentAgent(BaseAgent):
    """用户意图识别代理，用于识别用户输入并确定需要调用的代理类型"""
    
    # 已开发的代理类型
    AGENT_TYPES = {
        "data_analysis": {
            "name": "数据分析代理",
            "description": "执行数据分析任务，生成分析结果",
            "keywords": ["分析", "统计", "计算", "相关性", "聚类", "回归", "预测", "分组", "汇总", "平均", "求和"]
        },
        "data_visualization": {
            "name": "数据可视化代理",
            "description": "生成数据可视化图表，创建可视化HTML页面",
            "keywords": ["可视化", "图表", "绘制", "画图", "柱状图", "折线图", "饼图", "散点图", "热力图", "展示"]
        },
        "data_analysis_plan": {
            "name": "数据分析方案生成代理",
            "description": "根据数据信息和分析需求，生成合适的数据分析方案",
            "keywords": ["方案", "计划", "建议", "步骤", "流程", "思路", "策略", "规划", "设计", "指导"]
        },
        "data_analysis_conclusion": {
            "name": "数据分析结论代理",
            "description": "根据数据生成分析结论和见解",
            "keywords": ["结论", "见解", "洞察", "发现", "总结", "趋势", "特点", "规律", "意义", "启示", "解读"]
        }
    }
    
    def __init__(self, service_type: Optional[str] = None, model: Optional[str] = None):
        # 调用基类初始化，传入agent_id
        super().__init__(agent_id="user_intent", service_type=service_type, model=model)
    
    def execute(self, inputs: List[Any], user_prompt: str) -> Dict[str, Any]:
        """
        执行用户意图识别
        
        Args:
            inputs: 输入对象列表（在意图识别阶段不使用）
            user_prompt: 用户输入的提示文本
            
        Returns:
            包含识别结果的字典
        """
        # 构建提示信息
        messages = [
            {
                "role": "system",
                "content": """你是一个用户意图识别专家，能够准确理解用户的需求并分类。
请分析用户输入，判断用户想要执行的是数据分析任务、数据可视化任务、数据分析方案还是数据分析结论。
只返回一个JSON格式的结果，包含agent_type和confidence字段。"""
            },
            {
                "role": "user",
                "content": f"""
请分析以下用户输入，判断用户想要执行的任务类型：

用户输入: "{user_prompt}"

可选的任务类型:
1. data_analysis - 数据分析任务：执行数据分析、统计计算、相关性分析、聚类分析等
2. data_visualization - 数据可视化任务：生成图表、绘制可视化效果等
3. data_analysis_plan - 数据分析方案：生成数据分析方案、分析思路、分析步骤等
4. data_analysis_conclusion - 数据分析结论：生成数据分析结论、见解、洞察、趋势总结等

请以JSON格式返回结果，包含以下字段：
1. agent_type: 任务类型，必须是"data_analysis"、"data_visualization"、"data_analysis_plan"或"data_analysis_conclusion"之一
2. confidence: 置信度，0到1之间的小数
3. explanation: 简短解释为什么选择这个任务类型

只返回JSON格式的结果，不要有其他文字。
"""
            }
        ]
        
        # 调用LLM进行意图识别
        response = self.get_llm_service().chat_completion(messages=messages)
        raw_content = response['choices'][0]['message']['content']
        
        # 提取JSON结果
        result = self._extract_json_from_response(raw_content)
        
        # 如果LLM未返回有效结果，使用规则匹配作为备选方案
        if not result or 'agent_type' not in result:
            result = self._rule_based_intent_recognition(user_prompt)
        
        # 添加原始用户输入到结果中
        result['user_prompt'] = user_prompt
        
        return result
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """从LLM响应中提取JSON结果"""
        try:
            # 尝试直接解析整个响应
            import json
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取JSON部分
            json_pattern = re.compile(r'```(?:json)?\s*([\s\S]*?)\s*```')
            matches = json_pattern.findall(response_text)
            
            if matches:
                try:
                    return json.loads(matches[0])
                except json.JSONDecodeError:
                    pass
            
            # 尝试查找花括号包围的内容
            brace_pattern = re.compile(r'{[\s\S]*?}')
            matches = brace_pattern.findall(response_text)
            
            if matches:
                try:
                    return json.loads(matches[0])
                except json.JSONDecodeError:
                    pass
        
        return {}
    
    def _rule_based_intent_recognition(self, user_prompt: str) -> Dict[str, Any]:
        """使用规则匹配进行意图识别（作为备选方案）"""
        user_prompt = user_prompt.lower()
        scores = {}
        
        # 计算每种代理类型的匹配分数
        for agent_type, info in self.AGENT_TYPES.items():
            score = 0
            for keyword in info["keywords"]:
                if keyword.lower() in user_prompt:
                    score += 1
            
            # 归一化分数
            scores[agent_type] = score / len(info["keywords"]) if score > 0 else 0
        
        # 选择得分最高的代理类型
        if not scores or max(scores.values()) == 0:
            # 如果没有匹配项，默认为数据分析
            agent_type = "data_analysis"
            confidence = 0.5
            explanation = "未找到明确的意图指示，默认使用数据分析代理"
        else:
            agent_type = max(scores, key=scores.get)
            confidence = scores[agent_type]
            explanation = f"根据关键词匹配，识别为{self.AGENT_TYPES[agent_type]['name']}"
        
        return {
            "agent_type": agent_type,
            "confidence": confidence,
            "explanation": explanation
        }
