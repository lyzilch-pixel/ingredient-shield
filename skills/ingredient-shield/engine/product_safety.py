"""日化个护风险物质分析引擎。

基于统一危害注册表，对日化个护产品做致敏原 / 风险物质标注，并按物质类型给出风险等级：
- high：甲醛释放体、煤焦油染发剂等关注度高者
- warn：香精、SLS、 parabens、三氯生、邻苯二甲酸酯、氧苯酮、BHA/BHT 等一般关注

与食品过敏原逻辑共用 component_db，保证"成分 → 危害"映射一致。
"""
from . import component_db

# 风险等级（仅用于演示展示优先级，不代表医学结论）
HIGH_SUBSTANCES = {"formaldehyde_releaser", "coal_tar"}


def analyze(item):
    """对日化个护产品做风险物质标注。

    返回 {
      "flags": [{"id","name","level"}],
      "risk_count": int,
    }
    """
    a = component_db.analyze_item(item)
    flags = []
    for hid in set(a["contains"]) | set(a["may_contain"]):
        meta = component_db.get_hazard(hid)
        if not meta:
            continue
        if meta["category"] not in ("sensitizer", "substance"):
            continue
        level = "high" if hid in HIGH_SUBSTANCES else "warn"
        flags.append({"id": hid, "name": meta["zh"], "level": level})
    return {"flags": flags, "risk_count": len(flags)}


if __name__ == "__main__":
    item = {"id": "wipes-d", "name": "婴儿手口湿巾", "category": "daily_chem",
            "components": ["水", "甘油", "甲基异噻唑啉酮", "dmdm乙内酰脲"]}
    print(analyze(item))
