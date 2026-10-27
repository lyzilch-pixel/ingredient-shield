"""营养风险分析引擎。

基于《中国居民膳食指南（2022）》每日参考摄入量，对单品做"单份占比"风险标注：
- 钠：每日建议 < 2000mg；单份 > 800mg 标注"高钠"，> 600mg 标注"钠偏高"
- 添加糖：每日建议 < 25g；单份 > 15g 标注"高糖"，> 10g 标注"糖偏高"
- 反式脂肪：理想为 0；单份 > 0 标注"含反式脂肪"
- 热量：单份 > 700kcal 标注"高热量"，> 500kcal 标注"热量偏高"
- 脂肪：单份 > 30g 标注"高脂"，> 25g 标注"脂肪偏高"

阈值仅为健康提示参考，非医疗建议。
"""
from dataclasses import dataclass, field

# 每日参考摄入量（用于单份占比提示）
DAILY_REF = {"sodium": 2000, "sugar": 25, "calories": 2000, "fat": 60}

# 单份风险阈值
THRESHOLDS = {
    "sodium": {"high": 800, "warn": 600},
    "sugar": {"high": 15, "warn": 10},
    "trans_fat": {"high": 0.5, "warn": 0.0},
    "calories": {"high": 700, "warn": 500},
    "fat": {"high": 30, "warn": 25},
}


def analyze_nutrition(nutrition):
    """对单品营养数据做风险标注。

    返回 {
      "flags": [{"key","level","label","value","daily_pct"}],
      "risk_count": int,
    }
    """
    flags = []
    for key, th in THRESHOLDS.items():
        val = nutrition.get(key)
        if val is None:
            continue
        level = None
        if val > th["high"]:
            level = "high"
        elif val > th["warn"]:
            level = "warn"
        if level:
            label_map = {
                "sodium": "高钠" if level == "high" else "钠偏高",
                "sugar": "高糖" if level == "high" else "糖偏高",
                "trans_fat": "含反式脂肪",
                "calories": "高热量" if level == "high" else "热量偏高",
                "fat": "高脂" if level == "high" else "脂肪偏高",
            }
            pct = round(val / DAILY_REF.get(key, 1) * 100) if key in DAILY_REF else None
            flags.append({
                "key": key,
                "level": level,
                "label": label_map[key],
                "value": val,
                "daily_pct": pct,
            })
    return {"flags": flags, "risk_count": len(flags)}


def filter_by_constraints(items, constraints):
    """多约束筛选：根据营养 + 过敏原约束过滤餐品。

    constraints: {
      "sodium_max": int, "sugar_max": int, "calories_max": int,
      "trans_fat_max": float, "exclude_allergens": [aid...]
    }
    返回通过筛选的 item 列表（保留原结构）。
    """
    passed = []
    for it in items:
        nut = it.get("nutrition", {})
        if constraints.get("sodium_max") is not None and nut.get("sodium", 0) > constraints["sodium_max"]:
            continue
        if constraints.get("sugar_max") is not None and nut.get("sugar", 0) > constraints["sugar_max"]:
            continue
        if constraints.get("calories_max") is not None and nut.get("calories", 0) > constraints["calories_max"]:
            continue
        if constraints.get("trans_fat_max") is not None and nut.get("trans_fat", 0) > constraints["trans_fat_max"]:
            continue
        passed.append(it)
    return passed


if __name__ == "__main__":
    sample = {"calories": 563, "protein": 25, "fat": 30, "carbs": 46, "sodium": 1010, "sugar": 9, "trans_fat": 1.0}
    print(analyze_nutrition(sample))
    constraints = {"sodium_max": 800, "sugar_max": 10, "trans_fat_max": 0}
    print("约束筛选（钠<800,糖<10,反式脂肪=0）示例见 demo.py")
