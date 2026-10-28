"""跨品类组合风险引擎（与前端 analyzeCombinations 对齐）。

在单品分析之上，识别跨品类 / 跨产品的叠加暴露：
- 酒精：服用药品期间（禁酒 / 驾驶禁忌）接触含酒精的食品或日化
- 水杨酸叠加：内服含水杨酸类药品 + 外用含水杨酸日化
- 孕期：孕期状态 + 日化风险物质（染发剂 / 维A类 / 甲醛释放体）

结论仅作提示，非医疗建议。
"""
from .component_db import analyze_item, _normalize_component

ALCOHOL_TOKENS = ("酒精", "乙醇")
COMBO_RISKY_CHEM = ("coal_tar", "retinol", "formaldehyde_releaser")
# C：药品相互作用知识库（与前端 DRUG_INTERACTIONS 对齐）。
# a/b 可为危害 id（如 aspirin）或成分关键词（如 碳酸钙）
# a/b 使用真实数据中的成分关键词（与前端 DRUG_INTERACTIONS 对齐）。
# 注意：实际产品成分以中文登记（如 布洛芬 / 左氧氟沙星 / 红霉素），
# 这些英文 hazard id 既不在 COMPONENT_RULES 中、也无法作为子串命中中文成分，
# 因此这里统一用中文成分关键词，确保 _drug_match 子串回退能命中。
DRUG_INTERACTIONS = [
    {"a": "aspirin", "b": "布洛芬", "level": "warn", "title": "阿司匹林 + 布洛芬",
     "detail": "同属 NSAID，联用增加消化道出血与肾损伤风险，避免同时服用。"},
    {"a": "左氧氟沙星", "b": "布洛芬", "level": "block", "title": "左氧氟沙星 + 布洛芬",
     "detail": "氟喹诺酮类与 NSAID 联用增加中枢神经系统不良反应及肌腱断裂风险。"},
    {"a": "左氧氟沙星", "b": "aspirin", "level": "warn", "title": "左氧氟沙星 + 阿司匹林",
     "detail": "氟喹诺酮类与 NSAID 联用增加不良反应风险，请遵医嘱。"},
    {"a": "碳酸钙", "b": "左氧氟沙星", "level": "warn", "title": "钙剂 + 左氧氟沙星",
     "detail": "钙 / 镁 / 铁剂与喹诺酮类抗生素同服显著减少吸收，建议间隔 2 小时。"},
    {"a": "碳酸钙", "b": "红霉素", "level": "warn", "title": "钙剂 + 红霉素",
     "detail": "钙剂可能影响大环内酯类吸收，建议间隔服用。"},
]


def _drug_match(it, token):
    """判断药品 it 是否命中相互作用项 token（危害 id 或成分关键词，与前端 _drugMatch 对齐）。"""
    if token in analyze_item(it)["contains"]:
        return True
    n = _normalize_component(token)
    return any(n in _normalize_component(c) for c in it.get("components", []))


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

    # 4) 药品相互作用（C）：清单内两种药品存在已知相互作用
    for inter in DRUG_INTERACTIONS:
        a_hits = [it for it in drugs if _drug_match(it, inter["a"])]
        b_hits = [it for it in drugs if _drug_match(it, inter["b"])]
        if a_hits and b_hits:
            names = sorted({it["name"] for it in (a_hits + b_hits)})
            warns.append({"level": inter["level"], "title": "药品相互作用：" + inter["title"],
                          "detail": inter["detail"] + "（涉及：" + "、".join(names) + "）"})

    return warns
