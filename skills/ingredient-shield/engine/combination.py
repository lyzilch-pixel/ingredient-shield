"""跨品类组合风险引擎（与前端 analyzeCombinations 对齐）。

在单品分析之上，识别跨品类 / 跨产品的叠加暴露：
- 酒精：服用药品期间（禁酒 / 驾驶禁忌）接触含酒精的食品或日化
- 水杨酸叠加：内服含水杨酸类药品 + 外用含水杨酸日化
- 孕期：孕期状态 + 日化风险物质（染发剂 / 维A类 / 甲醛释放体）

结论仅作提示，非医疗建议。
"""
from .component_db import analyze_item

ALCOHOL_TOKENS = ("酒精", "乙醇")
COMBO_RISKY_CHEM = ("coal_tar", "retinol", "formaldehyde_releaser")


def analyze_combinations(items, profile):
    """items：归一化后的产品列表（含 category / components / contraindications）。
    profile：SafetyProfile（conditions 列表）。
    返回 [{"level","title","detail"}]
    """
    warns = []
    drugs = [it for it in items if it.get("category") == "drug"]
    chems = [it for it in items if it.get("category") == "daily_chem"]
    others = [it for it in items if it.get("category") != "drug"]

    conds = set(profile.conditions)
    drug_contra = set()
    for d in drugs:
        drug_contra.update(d.get("contraindications") or [])

    def has_cond(c):
        return c in conds or c in drug_contra

    def _contains(it):
        return analyze_item(it)["contains"]

    # 1) 酒精
    alcohol_items = [
        it for it in others
        if any(tok in (c or "") for c in it.get("components", []) for tok in ALCOHOL_TOKENS)
    ]
    if alcohol_items and (has_cond("alcohol") or has_cond("driving")):
        names = "、".join(it["name"] for it in alcohol_items)
        title = "服药驾驶 + 含酒精产品" if has_cond("driving") else "服药禁酒 + 含酒精产品"
        warns.append({"level": "block", "title": title,
                      "detail": f"含酒精：{names}。酒精会干扰药效或加重中枢抑制，请避免同用。"})

    # 2) 水杨酸叠加
    drug_aspirin = [it for it in drugs if "aspirin" in _contains(it)]
    chem_aspirin = [it for it in chems if "aspirin" in _contains(it)]
    if drug_aspirin and chem_aspirin:
        dn = "、".join(it["name"] for it in drug_aspirin)
        cn = "、".join(it["name"] for it in chem_aspirin)
        warns.append({"level": "warn", "title": "水杨酸叠加暴露",
                      "detail": f"药品 {dn} 与日化 {cn} 均含水杨酸类，内服+外用叠加需留意。"})

    # 3) 孕期跨品类：仅看用户画像（是否怀孕），不因清单内有"孕妇慎用"药品而对非孕用户报警
    if "pregnancy" in conds:
        risky = [it for it in chems if any(h in _contains(it) for h in COMBO_RISKY_CHEM)]
        if risky:
            cn = "、".join(it["name"] for it in risky)
            warns.append({"level": "block", "title": "孕期接触风险物质",
                          "detail": f"日化 {cn} 含孕期需谨慎成分（染发剂/维A类/甲醛释放体），请遵医嘱。"})

    return warns
