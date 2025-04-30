# BA_BunnyGachaEmulator

## 简介
随便写的抽卡模拟，图一乐
## 使用
Model1和Model2分别为两种发牌模型
TOTAL_TOKENS每次抽取的代币
NUM_SIMULATIONS模拟次数

    TOTAL_TOKENS = 120000
    NUM_SIMULATIONS = 100
    # 创建模拟抽卡类
    simulation = Simulation(TOTAL_TOKENS, NUM_SIMULATIONS, Model1)
    # 调用simulate_strategies()获取抽牌数和奖励统计
    average_results, average_rewards = simulation.simulate_strategies()
    # 分析
    print_strategy_differences(average_results, average_rewards)

添加策略请修改`Simulation`类下的`strategies`和`draw_cards()`
