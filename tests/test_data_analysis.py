from app.agents.data_analysis_agent import DataAnalysisAgent
from app.utils.data_loader import DataLoader
import pandas as pd

def test_data_analysis():
    # 初始化数据分析代理
    agent = DataAnalysisAgent()
    
    # 测试文件路径
    file_path = "/Users/haihuang.hh/Documents/code/interactive_data_analysis/data/sample.xlsx"
    
    # 测试分析需求
    analysis_requirement = """
    请对数据进行以下分析：
    1. 计算所有数值列的基本统计信息（均值、标准差、最大值、最小值）
    2. 对于分类列，计算每个类别的数量和占比
    3. 分析数据中的缺失值情况
    4. 如果存在时间列，请分析数据的时间分布
    """
    
    try:
        # 方法1：直接传入文件路径
        print("\n=== 测试方法1：直接传入文件路径 ===")
        result_dict = agent.execute([file_path], analysis_requirement)
        
        # 打印分析结果
        print("\n分析结果包含以下内容：")
        for key, df in result_dict.items():
            print(f"\n--- {key} ---")
            print(df.head())
        
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
        result_dict2 = agent.execute([df, df2], "比较这两个数据集的差异")
        
        # 打印分析结果
        print("\n分析结果包含以下内容：")
        for key, df in result_dict2.items():
            print(f"\n--- {key} ---")
            print(df.head())
        
    except Exception as e:
        print(f"分析过程中出现错误: {str(e)}")

if __name__ == "__main__":
    test_data_analysis()