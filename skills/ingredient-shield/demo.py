"""成分避雷 CLI 演示。

验证跨品类用户故事（US-1 ~ US-5）。运行：
    python demo.py

使用本地可插拔数据源（data/products.json），无需任何 Token。
"""
from engine import rules, provenance, safety_alert, nutrition
from engine.data_source import get_client
from engine.profile import from_inputs


def _print_header(t):
    print("\n" + "=" * 60)
    print(t)
    print("=" * 60)


def main():
    client = get_client("local")
    products = client.list_products()

    # US-1：食品过敏体质用户（花生 + 麸质）查询风险食品
    _print_header("US-1 食品过敏体质（花生 + 麸质过敏）")
    profile = from_inputs(hazard_ids=["peanuts", "gluten"])
    rec = rules.recommend_for_profile(products, profile)
    food = rec.get("food", {})
    print(f"✅ 安全食品（{len(food.get('safe', []))}）：", [s["name"] for s in food.get("safe", [])])
    print(f"⚠️ 留意（{len(food.get('warn', []))}）：", [(w["name"], w["hazard_names"]) for w in food.get("warn", [])])
    print(f"⛔ 已排除（{len(food.get('block', []))}）：", [(b["name"], b["hazard_names"]) for b in food.get("block", [])])

    # US-2：日化个护敏感用户（对 MIT + 香精敏感）查询风险产品
    _print_header("US-2 日化敏感（甲基异噻唑啉酮 + 香精）")
    profile = from_inputs(hazard_ids=["mit", "fragrance"])
    rec = rules.recommend_for_profile(products, profile)
    dc = rec.get("daily_chem", {})
    print(f"⛔ 含风险物质的日化（{len(dc.get('block', [])) + len(dc.get('warn', []))}）：")
    for ev in dc.get("block", []) + dc.get("warn", []):
        print(f"  - {ev['name']}：{ev['reasons']}")

    # US-3：孕期用户查询禁忌药品
    _print_header("US-3 孕期用户（健康状态：孕期）")
    profile = from_inputs(conditions=["pregnancy"])
    rec = rules.recommend_for_profile(products, profile)
    drug = rec.get("drug", {})
    print(f"⛔ 孕期禁忌药品（{len(drug.get('block', []))}）：")
    for ev in drug.get("block", []):
        print(f"  - {ev['name']}：{ev['reasons']}")
    print(f"✅ 可服用（{len(drug.get('safe', []))}）：", [s["name"] for s in drug.get("safe", [])])

    # US-4：跨品类召回 / 预警订阅（近 24h）
    _print_header("US-4 跨品类召回预警（近 24h）")
    alerts = safety_alert.recent_alerts(24)
    if alerts:
        for a in alerts:
            print(f"  [{a.get('category')}/{a['level']}] {a['title']}（采集 {a['collected_at']}）")
            print(f"      建议：{a['advice']}")
    else:
        print("近 24h 无新增预警。")

    # US-5：生成"我的安全消费清单"（跨品类分享卡数据）
    _print_header("US-5 生成「我的安全消费清单」（跨品类）")
    profile = from_inputs(
        hazard_ids=["peanuts", "mit", "penicillin"],
        conditions=["pregnancy"],
        nutrition_constraints={"sodium_max": 1000},
    )
    lst = rules.build_safety_list(products, profile)
    print("规避危害：", lst["user_hazards"])
    print("健康状态：", lst["user_conditions"])
    print(f"✅ 安全（{len(lst['safe'])}）：", [s["name"] for s in lst["safe"]])
    print(f"⚠️ 留意（{len(lst['warn'])}）：", [w["name"] for w in lst["warn"]])
    print(f"⛔ 排除（{len(lst['block'])}）：", [b["name"] for b in lst["block"]])
    print("声明：", lst["disclaimer"])


if __name__ == "__main__":
    main()
