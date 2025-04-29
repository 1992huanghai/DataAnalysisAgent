from app.agents.data_analysis_plan_agent import DataAnalysisPlanAgent
from app.utils.data_loader import DataLoader
import pandas as pd

def test_data_analysis_plan():
    # 初始化数据分析方案生成代理
    agent = DataAnalysisPlanAgent()
    
    # 测试文件路径
    file_path = "/Users/haihuang.hh/Documents/code/interactive_data_analysis/data/sample.xlsx"
    
    # 测试分析需求
    analysis_requirement = """
    我想了解这个数据集中的主要特征和模式，并找出可能影响销售额的因素。
    请给我一个全面的数据分析方案，包括应该使用哪些分析方法和可视化技术。
    """
    
    try:
        # 方法1：直接传入文件路径
        print("\n=== 测试方法1：直接传入文件路径 ===")
        result = agent.execute([file_path], analysis_requirement)
        
        # 打印分析方案
        print("\n分析方案：")
        print(result["plan"])
        
        # 方法2：先加载数据，再传入DataFrame
        print("\n=== 测试方法2：传入DataFrame ===")
        data_loader = DataLoader(file_path)
        df = data_loader.load_data()
        
        # 创建第二个测试DataFrame（示例）
        df2 = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': ['a', 'b', 'c', 'd', 'e']
        })
        
        # 传入多个DataFrame
        result2 = agent.execute([df, df2], "请为这两个数据集设计一个对比分析方案")
        
        # 打印分析方案
        print("\n对比分析方案：")
        print(result2["plan"])
        
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")

if __name__ == "__main__":
    test_data_analysis_plan()