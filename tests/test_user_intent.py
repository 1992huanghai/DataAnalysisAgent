from app.agents.user_intent_agent import UserIntentAgent

def test_user_intent():
    # 初始化用户意图识别代理
    agent = UserIntentAgent()
    
    # 测试各种用户输入
    test_prompts = [
        "帮我分析这个数据集的基本统计信息",
        "计算各列的平均值和标准差",
        "绘制销售数据的柱状图",
        "可视化用户增长趋势",
        "查看数据中的异常值",
        "生成各地区销售额的饼图",
        "分析两个变量之间的相关性",
        "展示不同类别的分布情况"
    ]
    
    print("\n=== 用户意图识别测试 ===")
    
    for prompt in test_prompts:
        try:
            # 执行意图识别
            result = agent.execute([], prompt)
            
            # 打印结果
            print(f"\n用户输入: {prompt}")
            print(f"识别结果: {result['agent_type']}")
            print(f"置信度: {result['confidence']:.2f}")
            print(f"解释: {result.get('explanation', '无')}")
            
        except Exception as e:
            print(f"识别过程中出现错误: {str(e)}")

if __name__ == "__main__":
    test_user_intent()