import random

# 设定奖项和对应概率
prizes = {
    '大吉': {
        'coins': 2500000,
        'shards': 5,
        'stones': 5,
        'base_prob': 0.05
    },
    '吉': {
        'coins': 2000000,
        'shards': 2,
        'stones': 3,
        'base_prob': 0.2
    },
    '中吉': {
        'coins': 1500000,
        'shards': 1,
        #'stones_prob': 0.5,  # 有50%的几率获得一个母猪石
        'stones': 2,
        'base_prob': 0.25
    },
    '小吉': {
        'coins': 1000000,
        'shards': 1,
        'stones': 1,
        'base_prob': 0.29
    },
    '末吉': {
        'coins': 500000,
        'shards': 1,
        'stones': 1,
        'base_prob': 0.20
    },
    '凶': {
        'shards': 5,
        'base_prob': 0.01
    }
}

def simulate_draw(total_draws):
    total_coins = 0
    total_shards = 0
    total_stones = 0
    draws_count = 0
    flag = 0

    probabilities = [prizes[name]['base_prob'] for name in prizes.keys()]

    for _ in range(total_draws):
        if draws_count == 15:
            draws_count = 0
            random_choice = 0  # 大吉的索引，每15次一定会抽到大吉
        else:
            random_choice = random.choices(range(6), weights=probabilities)[0]

        result = list(prizes.keys())[random_choice]
        if result == '大吉':
            flag += 1
        prize_data = prizes[result]

        # 累加奖励
        total_coins += prize_data.get('coins', 0)
        total_shards += prize_data.get('shards', 0)
        if 'stones_prob' in prize_data and random.random() < prize_data['stones_prob']:
            total_stones += prize_data['stones']
        else:
            total_stones += prize_data.get('stones', 0)

        if result == '大吉':
            draws_count = 0
            probabilities = [prizes[name]['base_prob'] for name in prizes.keys()]
        else:
            draws_count += 1
            # 更新概率
            if draws_count > 5:
                for i in range(6):
                    if i == 0:  # 大吉
                        probabilities[i] += 0.095
                    elif i == 1:  # 吉
                        probabilities[i] -= 0.02
                    elif i == 2 :  # 中吉、小吉
                        probabilities[i] -= 0.025
                    elif i == 3:  # 中吉、小吉
                        probabilities[i] -= 0.029
                    elif i == 4:  # 末吉
                        probabilities[i] -= 0.020
                    elif i == 5:  # 凶
                        probabilities[i] -= 0.001
                    probabilities[i] = max(probabilities[i], 0)
                prob_sum = sum(probabilities)
                tolerance = 1e-9
                if not (1 - tolerance <= prob_sum <= 1 + tolerance):
                    raise ValueError(f"概率之和不为1: {prob_sum}")
                probabilities = [p / prob_sum for p in probabilities]
    print(flag)
    return total_coins / total_draws, total_shards / total_draws, total_stones / total_draws

average_coins, average_shards, average_stones = simulate_draw(1000000)

print(f"平均每次抽卡获得的金币: {average_coins}")
print(f"平均每次抽卡获得的角色碎片: {average_shards}")
print(f"平均每次抽卡获得的母猪石: {average_stones}")