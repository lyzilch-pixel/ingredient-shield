"""跨品类危害知识库引擎。

加载 components.json（统一危害注册表）：
- hazards：危害定义（食品过敏原 / 日化致敏原 / 药品过敏 / 健康禁忌）
- component_hazard_rules：成分 / 配料 → 危害 id 映射
- cross_contact_risks：食品交叉污染风险

对外能力（品类无关，覆盖食品 / 日化个护 / 药品）：
- 根据产品成分推导确定性危害（contains）与交叉污染"可能含"（may_contain）
- 匹配用户危害画像，标注风险（排除 / 留意）
- 按品类返回危害集合（用于前端分组展示）

数据来自公开资料整理的开源知识库，非官方数据，仅供参考，不构成医疗 / 用药 / 法律建议。
"""
import json
import os
import re

_DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PATH = os.path.join(_DATA_DIR, "data", "components.json")


def _load():
    with open(_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_DB = _load()

HAZARD_INDEX = {h["id"]: h for h in _DB["hazards"]}
COMPONENT_RULES = _DB["component_hazard_rules"]
CROSS_CONTACT = _DB["cross_contact_risks"]


def get_hazard(id_):
    return HAZARD_INDEX.get(id_)


def list_hazards(category=None):
    if category:
        return [h for h in _DB["hazards"] if h["category"] == category]
    return _DB["hazards"]


def hazard_category(id_):
    h = HAZARD_INDEX.get(id_)
    return h["category"] if h else None


# 否定表述强标记（出现即视为"无/未添加"声明，不计入危害）
NEGATION_STRONG = ("不含", "未含", "未添加", "不添加", "无添加", "free", "zero")
# 子串匹配时排除的易误报单字键：麦（荞麦非麸质）、乳（乳酸/乳糖非乳源）、鱼（鱼香肉丝非鱼）
SUBSTRING_BLOCKED_SINGLE = {"麦", "乳", "鱼"}
# 可作为子串匹配的安全单字键
SUBSTRING_SAFE_SINGLE = {"蛋", "虾", "蟹"}
_HAZARD_KEYWORDS = set(COMPONENT_RULES.keys()) | set(HAZARD_INDEX.keys())


def _normalize_component(c):
    """成分名归一化：去括号及说明、去标点/分隔符、转小写，便于稳健匹配。"""
    c = (c or "").strip()
    c = re.sub(r"[（(][^)）]*[)）]", "", c)  # 去掉（说明）
    c = re.sub(r"[，,、\s]", "", c)
    return c.lower()


def _is_negation(norm):
    """判断归一化后的成分是否为否定/无添加声明。"""
    if any(m in norm for m in NEGATION_STRONG):
        return True
    # "无 + 危害关键词" 视为否定声明（无牛奶 / 无麸质），避免误报
    if "无" in norm and any(k and k in norm for k in _HAZARD_KEYWORDS):
        return True
    return False


def match_hazards(component_list):
    """根据成分列表推导确定性危害集合（精确匹配 + 安全子串 + 否定识别）。

    返回 {hazard_id: [触发成分...]}
    """
    result = {}
    for comp in component_list or []:
        norm = _normalize_component(comp)
        if not norm or _is_negation(norm):
            continue
        # 1) 精确匹配
        if norm in COMPONENT_RULES:
            for hid in COMPONENT_RULES[norm]:
                if hid:
                    result.setdefault(hid, []).append(comp)
        # 2) 安全子串匹配（多字键全开；单字键仅放行安全集）
        for key, hids in COMPONENT_RULES.items():
            if not hids or key == norm:
                continue
            if len(key) == 1 and key not in SUBSTRING_SAFE_SINGLE:
                continue
            if key in norm:
                for hid in hids:
                    if hid:
                        result.setdefault(hid, []).append(comp)
    return result


def match_cross_contact(component_list, name=""):
    """根据交叉污染规则推导"可能含"的危害集合。

    返回 {hazard_id: 风险说明}
    """
    text = (name or "") + " " + " ".join(component_list or [])
    result = {}
    for risk in CROSS_CONTACT:
        hit = any(kw in text for kw in risk.get("applies_to_keyword", []))
        if hit:
            for hid in risk.get("related_hazards", []):
                result.setdefault(hid, risk["note"])
    return result


def analyze_item(item):
    """分析单个产品的成分危害。

    返回 {
      "id","name","category",
      "contains": {hid:[成分]},
      "may_contain": {hid: 风险说明},
      "hazard_names": [zh...],
    }
    """
    components = item.get("components", [])
    contains = match_hazards(components)
    may_contain = match_cross_contact(components, item.get("name", ""))
    names = []
    for hid in set(contains) | set(may_contain):
        meta = HAZARD_INDEX.get(hid)
        if meta:
            names.append(meta["zh"])
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "category": item.get("category"),
        "contains": contains,
        "may_contain": may_contain,
        "hazard_names": names,
    }


def check_profile(item_analysis, user_hazard_ids):
    """检查产品是否触碰用户危害画像。

    user_hazard_ids：用户需规避的危害 id（过敏原 + 日化致敏原 + 药品过敏）
    返回 {"safe":bool,"blocked_by":[hid...],"warn_by":[hid...]}
    """
    blocked = [hid for hid in user_hazard_ids if hid in item_analysis["contains"]]
    warn = [
        hid
        for hid in user_hazard_ids
        if hid in item_analysis["may_contain"] and hid not in item_analysis["contains"]
    ]
    return {
        "safe": len(blocked) == 0,
        "blocked_by": blocked,
        "warn_by": warn,
    }


if __name__ == "__main__":
    sample = {"id": "peanut-butter", "name": "花生酱", "category": "food",
              "components": ["花生", "大豆油", "糖"]}
    a = analyze_item(sample)
    print("花生酱 危害：", a["hazard_names"])
    print("对花生+牛奶过敏：", check_profile(a, ["peanuts", "milk"]))
