"""日化个护风险物质分析引擎。

基于统一危害注册表，对日化个护产品做致敏原 / 风险物质标注，并按物质类型给出风险等级：
- high：甲醛释放体、煤焦油染发剂等关注度高者
- warn：香精、SLS、 parabens、三氯生、邻苯二甲酸酯、氧苯酮、BHA/BHT 等一般关注

D：支持浓度分级（当产品声明浓度 conc:{hazard_id: percent} 时，按阈值分级），
  无浓度声明则标注"浓度未标注"。阈值参考 SCCS/欧盟法规/国标典型限值，仅供参考非医疗建议。

H：可解释性 - 返回 reason_details：每条风险包含 type/level/text，映射 成分→危害 + 触发依据。

与食品过敏原逻辑共用 component_db，保证"成分 → 危害"映射一致。
"""
from . import component_db

# 风险等级（仅用于演示展示优先级，不代表医学结论）
HIGH_SUBSTANCES = {"formaldehyde_releaser", "coal_tar"}

# D：浓度阈值（% w/w，与前端 CHEM_CONC_THRESHOLD 对齐）
CHEM_CONC_THRESHOLD = {
    "formaldehyde_releaser": {"high": 0.2, "warn": 0.05},
    "coal_tar": {"high": 1.0, "warn": 0.1},
    "retinol": {"high": 1.0, "warn": 0.3},
    "oxybenzone": {"high": 6.0, "warn": 2.0},
    "triclosan": {"high": 0.3, "warn": 0.1},
    "mit": {"high": 0.01, "warn": 0.005},
    "parabens": {"high": 0.8, "warn": 0.4},
    "sls": {"high": 20, "warn": 5},
    "fragrance": {"high": 1.0, "warn": 0.1},
}


def _grade_conc(hid, conc_val):
    """按阈值给出分级：'high' / 'warn' / 'low' / 'undeclared'"""
    th = CHEM_CONC_THRESHOLD.get(hid)
    if not th or conc_val is None:
        return "undeclared"
    if conc_val >= th["high"]:
        return "high"
    if conc_val >= th["warn"]:
        return "warn"
    return "low"


def _explain_flags(analyzed_item, user_hazard_ids, profile_conditions, profile_nutri_constraints):
    """H：生成可解释性理由（与前端 evaluate 对齐）。

    返回 {
      "status": "safe|warn|block",
      "reasons": [str],           # 兼容旧逻辑的纯文本
      "reason_details": [         # 结构化可解释性
        {"type": "allergy|cross_contact|nutrition|substance|contraindication",
         "level": "warn|block",
         "text": "..."}
      ],
      "hazard_names": [zh...]
    }
    """
    a = analyzed_item
    reasons = []
    reason_details = []
    status = "safe"
    cat = a.get("category") or "unknown"
    contains = a.get("contains") or {}
    may_contain = a.get("may_contain") or {}
    nutrition = a.get("nutrition") or {}
    contraindications = a.get("contraindications") or []
    conc = a.get("conc") or {}

    # 1) 用户危害画像匹配
    blocked_haz = [hid for hid in user_hazard_ids if hid in contains]
    warn_haz = [hid for hid in user_hazard_ids if hid in may_contain and hid not in contains]

    if cat == "food":
        # 营养约束
        nut_fail = []
        for ckey, maxv in (profile_nutri_constraints or {}).items():
            if maxv is None:
                continue
            nkey = ckey[:-4] if ckey.endswith("_max") else ckey
            if nutrition.get(nkey) is not None and nutrition[nkey] > maxv:
                nut_fail.append((nkey, nutrition[nkey], maxv))

        if blocked_haz or nut_fail:
            status = "block"
        elif warn_haz:
            status = "warn"

        # 过敏原
        for hid in blocked_haz:
            meta = component_db.get_hazard(hid)
            comps = (contains.get(hid) or [])[:3]
            reason_details.append({
                "type": "allergy", "level": "block",
                "text": f"过敏原 {meta['zh'] if meta else hid}（来自：{'、'.join(comps)}）"
            })
        # 交叉接触
        for hid in warn_haz:
            meta = component_db.get_hazard(hid)
            comps = (may_contain.get(hid) or [])[:3]
            reason_details.append({
                "type": "cross_contact", "level": "warn",
                "text": f"可能含 {meta['zh'] if meta else hid}（交叉接触：{'、'.join(comps)}）"
            })
        # 营养
        for nkey, val, maxv in nut_fail:
            labels = {"sodium": "钠", "sugar": "糖", "trans_fat": "反式脂肪", "calories": "热量", "fat": "脂肪"}
            reason_details.append({
                "type": "nutrition", "level": "block",
                "text": f"营养约束未满足：{labels.get(nkey, nkey)} {val} 超过上限 {maxv}"
            })

    elif cat == "daily_chem":
        # 风险物质（sensitizer/substance）
        sub_flags = [hid for hid in set(contains) | set(may_contain)
                     if component_db.get_hazard(hid)
                     and component_db.get_hazard(hid)["category"] in ("sensitizer", "substance")]

        if blocked_haz:
            status = "block"
        elif warn_haz or sub_flags:
            status = "warn"

        for hid in sub_flags:
            meta = component_db.get_hazard(hid)
            comps = list(set(contains.get(hid) or []) | set(may_contain.get(hid) or []))[:3]
            th = CHEM_CONC_THRESHOLD.get(hid)
            if th and conc.get(hid) is not None:
                v = conc[hid]
                label = meta["zh"] if meta else hid
                if v >= th["high"]:
                    reason_details.append({
                        "type": "substance", "level": "block",
                        "text": f"高风险物质 {label}（浓度 {v}%≥{th['high']}%，来自：{'、'.join(comps)}）"
                    })
                elif v >= th["warn"]:
                    reason_details.append({
                        "type": "substance", "level": "warn",
                        "text": f"风险物质 {label}（浓度 {v}%≥{th['warn']}%，来自：{'、'.join(comps)}）"
                    })
                else:
                    reason_details.append({
                        "type": "substance", "level": "warn",
                        "text": f"风险物质 {label}（浓度 {v}%，来自：{'、'.join(comps)}）"
                    })
            else:
                reason_details.append({
                    "type": "substance",
                    "level": "warn" if hid in HIGH_SUBSTANCES else "warn",
                    "text": f"{'高风险物质' if hid in HIGH_SUBSTANCES else '风险物质'} {meta['zh'] if meta else hid}"
                            f"{f'(浓度 {conc[hid]}%)' if conc.get(hid) is not None else '(浓度未标注)'}"
                            f"（来自：{'、'.join(comps)}）"
                })

        for hid in blocked_haz:
            meta = component_db.get_hazard(hid)
            comps = (contains.get(hid) or [])[:3]
            reason_details.append({
                "type": "allergy", "level": "block",
                "text": f"致敏原 {meta['zh'] if meta else hid}（来自：{'、'.join(comps)}）"
            })
        for hid in warn_haz:
            meta = component_db.get_hazard(hid)
            comps = (may_contain.get(hid) or [])[:3]
            reason_details.append({
                "type": "cross_contact", "level": "warn",
                "text": f"可能含 {meta['zh'] if meta else hid}（交叉接触：{'、'.join(comps)}）"
            })

    elif cat == "drug":
        # 禁忌症
        b_cond = [c for c in contraindications if c in profile_conditions]
        b_haz = [hid for hid in user_hazard_ids if hid in contains]
        w_haz = [hid for hid in user_hazard_ids if hid in may_contain and hid not in contains]

        if b_cond or b_haz:
            status = "block"
        elif w_haz:
            status = "warn"

        for c in b_cond:
            meta = component_db.get_hazard(c)
            reason_details.append({
                "type": "contraindication", "level": "block",
                "text": f"禁忌 {meta['zh'] if meta else c}（健康状态：{meta['zh'] if meta else c}）"
            })
        for hid in b_haz:
            meta = component_db.get_hazard(hid)
            comps = (contains.get(hid) or [])[:3]
            reason_details.append({
                "type": "allergy", "level": "block",
                "text": f"成分过敏 {meta['zh'] if meta else hid}（来自：{'、'.join(comps)}）"
            })
        for hid in w_haz:
            meta = component_db.get_hazard(hid)
            comps = (may_contain.get(hid) or [])[:3]
            reason_details.append({
                "type": "cross_contact", "level": "warn",
                "text": f"可能含 {meta['zh'] if meta else hid}（交叉接触：{'、'.join(comps)}）"
            })

    else:
        status = "safe"

    # 兼容旧逻辑
    reasons = [r["text"] for r in reason_details]
    hazard_names = []
    for hid in set(contains) | set(may_contain):
        meta = component_db.get_hazard(hid)
        if meta:
            hazard_names.append(meta["zh"])

    return {"status": status, "reasons": reasons, "reason_details": reason_details, "hazard_names": hazard_names}


def analyze(item, user_hazard_ids=None, profile_conditions=None, profile_nutri_constraints=None):
    """对日化个护产品做风险物质标注（含 H 可解释性）。

    item 可选字段：conc = {hazard_id: percent, ...}

    返回 {
      "flags": [{"id","name","level","conc","grade"}],
      "risk_count": int,
      "status": "safe|warn|block",
      "reasons": [str],
      "reason_details": [...],
      "hazard_names": [zh...]
    }
    """
    a = component_db.analyze_item(item)
    # 合并 item 字段进去
    a["category"] = item.get("category", a.get("category"))
    a["nutrition"] = item.get("nutrition", a.get("nutrition"))
    a["contraindications"] = item.get("contraindications", a.get("contraindications"))
    a["conc"] = item.get("conc", a.get("conc", {}))

    flags = []
    conc = item.get("conc") or {}
    for hid in set(a["contains"]) | set(a["may_contain"]):
        meta = component_db.get_hazard(hid)
        if not meta:
            continue
        if meta["category"] not in ("sensitizer", "substance"):
            continue
        base_level = "high" if hid in HIGH_SUBSTANCES else "warn"
        conc_val = conc.get(hid)
        grade = _grade_conc(hid, conc_val)
        if base_level == "high" and grade == "high":
            level = "high"
        elif grade in ("high", "warn"):
            level = grade
        else:
            level = base_level
        flags.append({"id": hid, "name": meta["zh"], "level": level, "conc": conc_val, "grade": grade})

    # H：可解释性
    explain = _explain_flags(a, user_hazard_ids or [], profile_conditions or [], profile_nutri_constraints or {})

    return {"flags": flags, "risk_count": len(flags), **explain}


if __name__ == "__main__":
    # 测试：有浓度声明的产品
    item = {"id": "wipes-d", "name": "婴儿手口湿巾", "category": "daily_chem",
            "components": ["水", "甘油", "甲基异噻唑啉酮", "dmdm乙内酰脲"],
            "conc": {"formaldehyde_releaser": 0.15}}
    print("有浓度声明:", analyze(item))
    # 测试：无浓度声明
    item2 = {"id": "sunscreen-c", "name": "防晒喷雾", "category": "daily_chem",
             "components": ["水", "氧苯酮", "香精"]}
    print("无浓度声明:", analyze(item2))
    # 测试：高浓度 coal_tar + 过敏画像
    item3 = {"id": "hair-dye", "name": "染发剂", "category": "daily_chem",
             "components": ["水", "对苯二胺", "煤焦油", "香精"],
             "conc": {"coal_tar": 2.0}}
    print("高浓度染发剂:", analyze(item3, user_hazard_ids=["coal_tar"]))
