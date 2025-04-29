from app.agents.data_visualization_agent import DataVisualizationAgent
from app.utils.data_loader import DataLoader
import pandas as pd
import webbrowser
import os

def test_data_visualization():
    # 初始化数据可视化代理
    agent = DataVisualizationAgent()
    
    # 测试文件路径
    file_path = "/Users/haihuang.hh/Documents/code/interactive_data_analysis/data/sample.xlsx"
    
    # 测试可视化需求
    visualization_requirement = """
    请创建以下可视化图表：
    1. 所有数值列的分布直方图
    2. 如果有时间列，创建时间序列图表
    3. 如果有分类列，创建饼图显示各类别占比
    4. 创建一个交互式的散点图，允许用户选择X轴和Y轴的列
    """
    
    try:
        # 加载数据
        data_loader = DataLoader(file_path)
        df = data_loader.load_data()
        
        # 创建第二个测试DataFrame（示例数据）
        dates = pd.date_range('20230101', periods=100)
        df2 = pd.DataFrame({
            'date': dates,
            'value': [i * 2 + (i % 5) for i in range(100)],
            'category': [['A', 'B', 'C', 'D', 'E'][i % 5] for i in range(100)]
        })
        
        # 执行可视化
        html_path = agent.execute([df, df2], visualization_requirement)
        
        print(f"\n可视化HTML已生成: {html_path}")
        return html_path
        # 自动在浏览器中打开生成的HTML
        webbrowser.open(f"file://{os.path.abspath(html_path)}")
        
    except Exception as e:
        print(f"可视化过程中出现错误: {str(e)}")

if __name__ == "__main__":
    test_data_visualization()