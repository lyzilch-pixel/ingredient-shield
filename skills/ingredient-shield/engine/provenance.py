"""产品溯源 / 资质引擎（由旧的食材溯源引擎泛化而来）。

根据产品成分，匹配溯源 / 资质 / 认证知识库，返回产地、资质、认证摘要。
覆盖食品原料、日化原料、药品成分三类。数据非官方，仅作决策参考。
"""
import json
import os

_DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PATH = os.path.join(_DATA_DIR, "data", "provenance.json")

with open(_PATH, "r", encoding="utf-8") as f:
    _DB = json.load(f)

_RECORDS = _DB["records"]


def lookup_provenance(component_list):
    """返回与成分相关的溯源 / 资质记录列表。

    匹配规则：成分名称若包含某记录 key 的子串，或反之，即命中。
    """
    results = []
    for comp in component_list or []:
        comp = comp.strip()
        for rec in _RECORDS:
            key = rec["key"]
            if comp in key or key in comp:
                results.append(rec)
                break
    seen = set()
    unique = []
    for r in results:
        if r["key"] not in seen:
            seen.add(r["key"])
            unique.append(r)
    return unique


if __name__ == "__main__":
    print(lookup_provenance(["牛奶", "三文鱼", "花生"]))
