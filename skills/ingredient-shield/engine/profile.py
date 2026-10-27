"""跨品类个人安全画像。

将原本分散的"过敏画像 / 营养约束 / 健康状态"统一为一份结构化画像，
供 rules 在各品类上做一致性校验：
- hazard_ids：需规避的危害 id（食品过敏原 + 日化致敏原 + 药品过敏）
- conditions：健康状态 id（孕期 / 哺乳期 / 高血压 / 糖尿病 / 肾功能不全 / 未成年 / 服药禁酒 / 服药勿驾驶）
- nutrition_constraints：食品营养约束（钠 / 糖 / 反式脂肪 / 热量上限）

所有字段可选；画像仅在本会话 / 本地使用，不上传第三方。
"""
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class SafetyProfile:
    hazard_ids: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    nutrition_constraints: Dict[str, float] = field(default_factory=dict)

    def has_hazard(self, hid):
        return hid in self.hazard_ids

    def has_condition(self, cid):
        return cid in self.conditions


def from_inputs(hazard_ids=None, conditions=None, nutrition_constraints=None):
    """便捷构造器。"""
    return SafetyProfile(
        hazard_ids=hazard_ids or [],
        conditions=conditions or [],
        nutrition_constraints=nutrition_constraints or {},
    )


if __name__ == "__main__":
    p = from_inputs(
        hazard_ids=["peanuts", "milk", "mit"],
        conditions=["pregnancy"],
        nutrition_constraints={"sodium_max": 800, "sugar_max": 10, "trans_fat_max": 0},
    )
    print(p)
