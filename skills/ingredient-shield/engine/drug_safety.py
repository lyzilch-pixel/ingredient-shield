"""药品安全分析引擎。

对药品做两类校验：
1. 健康禁忌（condition）：药品 contraindications 与用户健康状态（孕期 / 哺乳期 / 高血压 /
   糖尿病 / 肾功能不全 / 未成年 / 服药禁酒 / 服药勿驾驶）求交集 → 禁忌命中。
2. 成分过敏（drug_allergy）：通过统一危害注册表检查药品成分是否触碰用户药品过敏
   （青霉素类 / 阿司匹林类 / 磺胺类）。

返回结构化结论，供 rules 编排为"排除 / 留意 / 安全"。
"""
from . import component_db


def analyze(item, user_conditions=None, user_hazard_ids=None):
    """分析单个药品。

    user_conditions：用户健康状态 id 列表
    user_hazard_ids：用户需规避的危害 id（含药品过敏）
    返回 {
      "blocked_conditions":[id...],
      "blocked_hazards":[id...],
      "warn_hazards":[id...],
      "blocked": bool,
      "reasons": [中文说明...],
    }
    """
    user_conditions = user_conditions or []
    user_hazard_ids = user_hazard_ids or []

    item_analysis = component_db.analyze_item(item)
    prof = component_db.check_profile(item_analysis, user_hazard_ids)

    blocked_conditions = [c for c in user_conditions if c in (item.get("contraindications") or [])]
    blocked_hazards = prof["blocked_by"]
    warn_hazards = prof["warn_by"]

    reasons = []
    for c in blocked_conditions:
        meta = component_db.get_hazard(c)
        reasons.append(f"禁忌：{meta['zh'] if meta else c}")
    for h in blocked_hazards:
        meta = component_db.get_hazard(h)
        reasons.append(f"成分过敏：{meta['zh'] if meta else h}")
    for h in warn_hazards:
        meta = component_db.get_hazard(h)
        reasons.append(f"可能含（交叉）：{meta['zh'] if meta else h}")

    blocked = len(blocked_conditions) > 0 or len(blocked_hazards) > 0
    return {
        "blocked_conditions": blocked_conditions,
        "blocked_hazards": blocked_hazards,
        "warn_hazards": warn_hazards,
        "blocked": blocked,
        "reasons": reasons,
    }


if __name__ == "__main__":
    item = {"id": "ibuprofen", "name": "布洛芬缓释胶囊", "category": "drug",
            "components": ["布洛芬", "淀粉"], "contraindications": ["pregnancy", "kidney"]}
    print(analyze(item, user_conditions=["pregnancy"], user_hazard_ids=[]))
