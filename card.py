import random
import sys
import time
from os import urandom
from pathlib import Path

import orjson

dir_path = Path(__file__).parent

cards = orjson.loads(open(dir_path / "cards.json", "rb").read())
CARD_LIST = []
CARD_PROB_LIST = []
SPECIAL_CARD_LIST = []
SPECIAL_CARD_PROB_LIST = []
CARD_INFO = {}

for id, card_info in cards.items():
    id = int(id)
    if card_info["card_EventContentId"] == 826:
        if card_info["card_refresh_group"] < 4:
            CARD_LIST.append(id)
            CARD_PROB_LIST.append(card_info["card_prob"] / 10000)
        else:
            SPECIAL_CARD_LIST.append(id)
            SPECIAL_CARD_PROB_LIST.append(card_info["card_prob"] / 10000)
        CARD_INFO[id] = card_info


class Card:
    def __init__(self, id):
        self.id = id
        self.card_type = CARD_INFO[id]["card_type"]
        self.card_reward = CARD_INFO[id]["card_reward"]
        self.name = CARD_INFO[id]["card_name"]


# 每次刷新生成四张 3张应用基础概率 1张应用保底概率 打乱后四个位置给玩家选
class Model1:
    @staticmethod
    def generate_cards():
        seed = time.time_ns() ^ int.from_bytes(urandom(8), "big")
        random.seed(seed)

        card_ids = random.choices(CARD_LIST, CARD_PROB_LIST, k=3) + random.choices(
            SPECIAL_CARD_LIST, SPECIAL_CARD_PROB_LIST
        )
        random.shuffle(card_ids)
        return [Card(cid) for cid in card_ids]


# 每一抽默认普通概率 如果抽到了金后 则该轮均为普通概率；如果前三抽没出金彩，第四抽应用保底概率
class Model2:
    @staticmethod
    def generate_cards():
        seed = time.time_ns() ^ int.from_bytes(urandom(8), "big")
        random.seed(seed)

        card_ids = random.choices(CARD_LIST, CARD_PROB_LIST, k=3)

        special_draw = True
        for cid in card_ids:
            if CARD_INFO[cid]["card_type"] in ["SR", "SSR"]:
                special_draw = False
                break

        if special_draw:
            card_id = random.choices(SPECIAL_CARD_LIST, SPECIAL_CARD_PROB_LIST)[0]
            card_ids.append(card_id)
        else:
            card_id = random.choices(CARD_LIST, CARD_PROB_LIST)[0]
            card_ids.append(card_id)
        # 得翻转一下，不然pop天天取保底牌了）
        card_ids.reverse()
        return [Card(cid) for cid in card_ids]


class Simulation:
    def __init__(self, total_tokens, num_simulations, choose_deck):
        self.total_tokens = total_tokens
        self.num_simulations = num_simulations
        self.token_costs = [200, 210, 220, 230]
        self.strategies = {
            1: "单抽后重置",
            2: "抽到金彩后重置",
            3: "抽到金后重置",
            4: "抽到彩后重置",
            5: "抽完四张后重置",
            6: "第一张金彩刷新，第二张固定刷新",
            7: "抽两张后刷新",
        }
        self.choose_deck = choose_deck

    def draw_cards(self, strategy):
        results_count = {"N": 0, "R": 0, "SR": 0, "SSR": 0}
        reward_summary = {}

        total_tokens = self.total_tokens

        while total_tokens > min(self.token_costs):
            cards = self.choose_deck.generate_cards()
            round_cost = 0

            for cost in self.token_costs:
                if total_tokens < cost:
                    break
                total_tokens -= cost
                round_cost += cost

                card = cards.pop()
                results_count[card.card_type] += 1

                # 获取对应的奖励
                for reward in card.card_reward:
                    reward_name = reward["reward_name"]
                    reward_amount = reward["reward_amount"]
                    if reward_name in reward_summary:
                        reward_summary[reward_name] += reward_amount
                    else:
                        reward_summary[reward_name] = reward_amount

                if (
                    strategy == 1
                    or (strategy == 2 and card.card_type in ["SR", "SSR"])
                    or (strategy == 3 and card.card_type == "SR")
                    or (strategy == 4 and card.card_type == "SSR")
                    or (strategy == 5 and len(cards) == 0)
                    or (strategy == 6 and card.card_type in ["SR", "SSR"])
                    or (strategy == 6 and len(cards) == 2)
                    or (strategy == 7 and len(cards) == 2)
                ):
                    break

            if round_cost == 0:
                break

        return results_count, reward_summary

    def simulate_strategies(self):
        strategy_results = {
            key: {"N": 0, "R": 0, "SR": 0, "SSR": 0} for key in self.strategies
        }
        strategy_rewards = {key: {} for key in self.strategies}

        for strategy in strategy_results:
            print(f"\n策略{strategy}: {self.strategies[strategy]}")
            for i in range(self.num_simulations):
                if (i + 1) % (self.num_simulations // 100) == 0:
                    progress_bar_length = 50
                    percent_done = (i + 1) / self.num_simulations
                    filled_length = int(progress_bar_length * percent_done)
                    bar = "=" * filled_length + "-" * (
                        progress_bar_length - filled_length
                    )
                    print(f"\r进度: [{bar}] {percent_done * 100:.2f}%", end="")
                    sys.stdout.flush()

                results, reward_summary = self.draw_cards(strategy)
                for type in results:
                    strategy_results[strategy][type] += results[type]

                for reward_name, reward_amount in reward_summary.items():
                    if reward_name in strategy_rewards[strategy]:
                        strategy_rewards[strategy][reward_name] += reward_amount
                    else:
                        strategy_rewards[strategy][reward_name] = reward_amount

            # 计算平均
            for type in strategy_results[strategy]:
                strategy_results[strategy][type] /= self.num_simulations

            for reward_name in strategy_rewards[strategy]:
                strategy_rewards[strategy][reward_name] /= self.num_simulations
            print("\n完成")

        return strategy_results, strategy_rewards


def print_colored_diff(value):
    prefix = "{:+.3f}"
    if value > 0:
        return "\033[92m" + prefix.format(value) + "\033[0m"
    elif value < 0:
        return "\033[94m" + prefix.format(value) + "\033[0m"
    else:
        return prefix.format(value)


def print_strategy_differences(average_results, average_rewards):
    base_strategy_num = 1  # 策略1作为基准

    base_results_formatted = {
        k: "{:.3f}".format(v) for k, v in average_results[base_strategy_num].items()
    }
    base_rewards_formatted = {
        k: "{:.3f}".format(v) for k, v in average_rewards[base_strategy_num].items()
    }
    print(f"\n策略{base_strategy_num}: {simulation.strategies[base_strategy_num]}")
    print("策略{}的平均抽卡结果:".format(base_strategy_num))
    for _ in base_results_formatted:
        total_cards = sum(
            [
                average_results[base_strategy_num][each]
                for each in base_results_formatted
            ]
        )
    for card, value in base_results_formatted.items():
        print(
            " {}: {}|{:.2f}%".format(
                card, value, float(value) / float(total_cards) * 100
            )
        )
    print("\n策略{}的平均奖励数量:".format(base_strategy_num))
    for reward, value in base_rewards_formatted.items():
        print(" {}: {}".format(reward, value))

    for strategy in average_results:
        if strategy == base_strategy_num:
            continue

        card_type_diff = {
            card_type: average_results[strategy][card_type]
            - average_results[base_strategy_num][card_type]
            for card_type in average_results[base_strategy_num]
        }
        print(f"\n策略{strategy}: {simulation.strategies[strategy]}")
        print("策略{}的结果 (相对于策略{}的差异):".format(strategy, base_strategy_num))
        print("抽卡差异:")
        for _ in base_results_formatted:
            total_cards = sum(
                [average_results[strategy][each] for each in base_results_formatted]
            )
        for card, diff in card_type_diff.items():
            diff_color = print_colored_diff(diff)
            print(
                f" {card}: {average_results[strategy][card]:.3f}|{float(average_results[strategy][card])/float(total_cards)*100:.2f}% ({diff_color})"
            )

        print("奖励物品平均数量差异:")
        for reward in set(average_rewards[base_strategy_num]) | set(
            average_rewards[strategy]
        ):
            strategy_value = average_rewards[strategy].get(reward, 0)
            base_value = average_rewards[base_strategy_num].get(reward, 0)
            diff = strategy_value - base_value
            diff_color = print_colored_diff(diff)
            print(f" {reward}: {strategy_value:.3f} ({diff_color})")


TOTAL_TOKENS = 34500
NUM_SIMULATIONS = 1000
simulation = Simulation(TOTAL_TOKENS, NUM_SIMULATIONS, Model1)
average_results, average_rewards = simulation.simulate_strategies()

print_strategy_differences(average_results, average_rewards)
