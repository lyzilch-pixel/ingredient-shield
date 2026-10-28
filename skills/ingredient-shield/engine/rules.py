"""规则编排引擎（跨品类对外主入口）。

将成分危害库、营养风险、日化风险物质、药品禁忌、溯源 / 资质、召回预警六个子能力
编排为面向用户场景的决策结果：
- 单品安全分析（按品类组装：危害 + 营养/物质/禁忌 + 溯源）
- 用户画像匹配（跨品类规避：过敏原 + 致敏原 + 药品过敏 + 健康禁忌 + 营养约束）
- 安全消费清单生成（供前端分享，跨品类汇总）

H：可解释性 - evaluate_item 返回 reason_details 结构化理由。

所有结论均附带"数据来自开源知识库，非官方，仅供参考"标识，符合合规要求。
"""
from . import component_db, nutrition, product_safety, drug_safety, provenance
from .profile import SafetyProfile


def evaluate_item(item, profile):
    """对单个产品做跨品类风险评定（含 H 可解释性）。

    返回 {
      "id","name","category",
      "status": "safe" | "warn" | "block",
      "hazard_names": [zh...],
      "reasons": [说明...],           # 兼容旧逻辑纯文本
      "reason_details": [...],        # H 结构化理由
      "analysis": 各品类附加分析,
    }
    """
    cat = item.get("category")
    hazard_ids = profile.hazard_ids
    conditions = profile.conditions
    nutri_constraints = profile.nutrition_constraints

    base = component_db.analyze_item(item)
    reasons = []
    reason_details = []

    if cat == "food":
        prof = component_db.check_profile(base, hazard_ids)
        nut = item.get("nutrition", {})
        cons = profile.nutrition_constraints
        nut_fail = []
        if cons.get("sodium_max") is not None and nut.get("sodium", 0) > cons["sodium_max"]:
            nut_fail.append(f"钠 {nut.get('sodium')}mg 超上限 {cons['sodium_max']}mg")
        if cons.get("sugar_max") is not None and nut.get("sugar", 0) > cons["sugar_max"]:
            nut_fail.append(f"糖 {nut.get('sugar')}g 超上限 {cons['sugar_max']}g")
        if cons.get("trans_fat_max") is not None and nut.get("trans_fat", 0) > cons["trans_fat_max"]:
            nut_fail.append("含反式脂肪")
        if cons.get("calories_max") is not None and nut.get("calories", 0) > cons["calories_max"]:
            nut_fail.append(f"热量 {nut.get('calories')}kcal 超上限 {cons['calories_max']}kcal")
        if cons.get("fat_max") is not None and nut.get("fat", 0) > cons["fat_max"]:
            nut_fail.append(f"脂肪 {nut.get('fat')}g 超上限 {cons['fat_max']}g")
        for r in nut_fail:
            reasons.append(f"营养约束：{r}")
        status = "block" if (prof["blocked_by"] or nut_fail) else ("warn" if prof["warn_by"] else "safe")
        analysis = {"nutrition_flags": nutrition.analyze_nutrition(nut)}

        # H：食品可解释性
        for hid in prof["blocked_by"]:
            meta = component_db.get_hazard(hid)
            comps = (base["contains"].get(hid) or [])[:3]
            reason_details.append({
                "type": "allergy", "level": "block",
                "text": f"过敏原 {meta['zh'] if meta else hid}（来自：{'、'.join(comps)}）"
            })
        for hid in prof["warn_by"]:
            meta = component_db.get_hazard(hid)
            comps = (base["may_contain"].get(hid) or [])[:3]
            reason_details.append({
                "type": "cross_contact", "level": "warn",
                "text": f"可能含 {meta['zh'] if meta else hid}（交叉接触：{'、'.join(comps)}）"
            })
        labels = {"sodium": "钠", "sugar": "糖", "trans_fat": "反式脂肪", "calories": "热量", "fat": "脂肪"}
        for ckey, maxv in cons.items():
            if maxv is None:
                continue
            nkey = ckey[:-4] if ckey.endswith("_max") else ckey
            if nut.get(nkey) is not None and nut[nkey] > maxv:
                reason_details.append({
                    "type": "nutrition", "level": "block",
                    "text": f"营养约束未满足：{labels.get(nkey, nkey)} {nut[nkey]} 超过上限 {maxv}"
                })

    elif cat == "daily_chem":
        # H：使用 product_safety.analyze（含 reason_details）
        ps = product_safety.analyze(
            item,
            user_hazard_ids=hazard_ids,
            profile_conditions=conditions,
            profile_nutri_constraints=nutri_constraints
        )
        reasons = ps["reasons"]           # 兼容旧逻辑
        reason_details = ps["reason_details"]  # H 结构化
        status = ps["status"]
        analysis = {"substance_flags": ps["flags"]}

    elif cat == "drug":
        ds = drug_safety.analyze(item, user_conditions=conditions, user_hazard_ids=hazard_ids)
        reasons = ds["reasons"]
        # H：药品可解释性（转为统一结构）
        reason_details = [
            {"type": "contraindication" if "禁忌" in r else ("allergy" if "过敏" in r else "cross_contact"),
             "level": "block" if "禁忌" in r or "过敏" in r else "warn",
             "text": r}
            for r in ds["reasons"]
        ]
        status = "block" if ds["blocked"] else ("warn" if ds["warn_hazards"] else "safe")
        analysis = {"drug": ds}
    else:
        prof = component_db.check_profile(base, hazard_ids)
        status = "block" if prof["blocked_by"] else ("warn" if prof["warn_by"] else "safe")
        analysis = {}

    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "category": cat,
        "status": status,
        "hazard_names": base["hazard_names"],
        "reasons": reasons,
        "reason_details": reason_details,
        "analysis": analysis,
    }


def analyze_item_full(item, profile=None):
    """对单品做完整安全分析（含溯源 / 资质）。"""
    profile = profile or SafetyProfile()
    ev = evaluate_item(item, profile)
    ev["provenance"] = provenance.lookup_provenance(item.get("components", []))
    return ev


def recommend_for_profile(products, profile):
    """为用户画像筛选跨品类安全产品。

    返回 {category: {"safe":[],"warn":[],"block":[]}}（仅含存在的品类）。
    """
    result = {}
    for it in products:
        ev = evaluate_item(it, profile)
        cat = ev["category"]
        result.setdefault(cat, {"safe": [], "warn": [], "block": []})
        result[cat][ev["status"]].append(ev)
    return result


def build_safety_list(products, profile):
    """生成"我的安全消费清单"（供分享卡使用），跨品类汇总。

    返回结构化清单：用户信息 + 各品类安全项 + 风险项 + 免责声明。
    """
    rec = recommend_for_profile(products, profile)
    hazard_names = [component_db.get_hazard(h)["zh"] for h in profile.hazard_ids if component_db.get_hazard(h)]
    cond_names = [component_db.get_hazard(c)["zh"] for c in profile.conditions if component_db.get_hazard(c)]

    def _summaries(bucket):
        return [{"name": ev["name"], "category": ev["category"],
                 "hazard_names": ev["hazard_names"], "reasons": ev["reasons"]} for ev in bucket]

    safe, warn, block = [], [], []
    for cat in rec:
        safe += _summaries(rec[cat]["safe"])
        warn += _summaries(rec[cat]["warn"])
        block += _summaries(rec[cat]["block"])

    return {
        "generated_at": "本地生成，未上传",
        "user_hazards": hazard_names,
        "user_conditions": cond_names,
        "nutrition_constraints": profile.nutrition_constraints,
        "safe": safe,
        "warn": warn,
        "block": block,
        "disclaimer": "数据来自开源知识库，非官方，仅供参考，不构成医疗、用药或法律建议。",
    }
