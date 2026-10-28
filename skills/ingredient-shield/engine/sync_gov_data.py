"""定期同步：从（可配置的）公开公告数据源清洗为标准 gov_products.json + 召回预警。

设计：
- 复用 engine/data_source.py 的 GovPublicDataSource（CSV/JSON 自动识别 + 字段归一化）。
- 数据源可插拔：
  * 默认（无 SOURCE_URL）：读取同目录 ../data/gov_feed_sample.csv（公开公告格式的样例 feed）。
  * 设置环境变量 SOURCE_URL 后：下载该地址的数据（支持 .json / .csv），用于接入你授权的真实官方 feed。
- 输出 ../data/gov_products.json，附 _meta.synced_at 与分类计数，供前端运行时拉取。
- J：同步召回/预警（可选 ALERTS_SOURCE_URL），输出 ../data/gov_alerts.json，前端显示同步时间 + 兜底本地演示数据。
- 仅做字段归一化与基础校验，不编造任何官方数据；真实接入请自备授权数据源。
"""
import os
import sys
import json
import argparse
import urllib.request
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from data_source import GovPublicDataSource  # noqa: E402

_DATA_DIR = os.path.join(_HERE, "..", "data")
SAMPLE_CSV = os.path.join(_DATA_DIR, "gov_feed_sample.csv")
DEFAULT_OUT = os.path.join(_DATA_DIR, "gov_products.json")
DEFAULT_ALERTS_OUT = os.path.join(_DATA_DIR, "gov_alerts.json")
COMPONENTS_JSON = os.path.join(_DATA_DIR, "components.json")


def _download(url: str) -> str:
    """下载 SOURCE_URL 到临时文件，返回本地路径（保留扩展名）。"""
    req = urllib.request.Request(url, headers={"User-Agent": "ingredient-shield-sync/1.0"})
    ext = ".csv" if url.lower().endswith(".csv") else ".json"
    tmp = os.path.join(_DATA_DIR, f"_gov_incoming{ext}")
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        data = resp.read()
    with open(tmp, "wb") as f:
        f.write(data)
    return tmp


def _category_counts(products):
    counts = {}
    for p in products:
        c = p.get("category", "unknown")
        counts[c] = counts.get(c, 0) + 1
    return counts


def _load_hazard_tokens():
    try:
        with open(COMPONENTS_JSON, "r", encoding="utf-8") as f:
            reg = json.load(f)
        return set(reg.get("component_hazard_rules", {}).keys())
    except FileNotFoundError:
        return set()


def _normalize_alert(a):
    """将预警条目归一化为标准结构。"""
    # 支持字段：id, category, level, title, scope/detail, collected_at, advice, is_demo
    return {
        "id": a.get("id"),
        "category": a.get("category"),
        "level": a.get("level"),
        "title": a.get("title"),
        "scope": a.get("scope") or a.get("detail"),
        "collected_at": a.get("collected_at"),
        "advice": a.get("advice"),
        "is_demo": a.get("is_demo", False),
    }


def run(source_url: str | None, out_path: str) -> dict:
    if source_url:
        print(f"[sync] 下载数据源：{source_url}")
        src_path = _download(source_url)
    else:
        print(f"[sync] 使用本地样例 feed：{SAMPLE_CSV}")
        src_path = SAMPLE_CSV

    ds = GovPublicDataSource(src_path)
    products = ds._products
    if not products:
        raise SystemExit("[sync] 未解析到任何产品，同步中止（未写入任何文件）。")

    counts = _category_counts(products)
    hazard_tokens = _load_hazard_tokens()
    matched = sum(
        1
        for p in products
        if hazard_tokens.intersection(set(p.get("components") or []))
    )

    meta = {
        "version": "2.1.0",
        "synced_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": source_url or ("local sample feed: gov_feed_sample.csv"),
        "disclaimer": "本文件由同步管线从公开公告格式数据清洗生成，为非官方演示数据，仅供参考，不构成医疗、用药或法律建议。",
        "counts": counts,
        "hazard_matched": matched,
        "total": len(products),
    }
    payload = {"_meta": meta, "products": products}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[sync] 已写入 {out_path}：共 {len(products)} 项，分类 {counts}，命中危害规则 {matched} 项。")
    return meta


def run_alerts(source_url: str | None, out_path: str) -> dict:
    """J：同步召回/预警数据（可选 ALERTS_SOURCE_URL），输出 gov_alerts.json。"""
    if source_url:
        print(f"[sync-alerts] 下载预警源：{source_url}")
        src_path = _download(source_url)
    else:
        # 兜底：读取本地演示数据
        local_alerts = os.path.join(_DATA_DIR, "safety_alerts.json")
        print(f"[sync-alerts] 使用本地演示预警：{local_alerts}")
        src_path = local_alerts

    try:
        with open(src_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("[sync-alerts] 预警源文件不存在，跳过。")
        return {"alerts_synced": 0, "fallback": True}

    alerts = data.get("alerts", []) if isinstance(data, dict) else data
    normed = [_normalize_alert(a) for a in alerts if a.get("category") in ("food", "daily_chem", "drug")]

    meta = {
        "version": "1.0.0",
        "synced_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": source_url or ("local demo alerts: safety_alerts.json"),
        "disclaimer": "本文件由同步管线从公开召回/预警公告清洗生成，为非官方演示数据，仅供参考。真实预警请以监管部门及品牌官方公告为准。",
        "total": len(normed),
    }
    payload = {"_meta": meta, "alerts": normed}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[sync-alerts] 已写入 {out_path}：共 {len(normed)} 条预警。")
    return {"alerts_synced": len(normed), "meta": meta}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT, help="输出 gov_products.json 路径")
    ap.add_argument("--source-url", default=os.environ.get("SOURCE_URL"), help="可选：远程产品数据源地址（.json/.csv）")
    ap.add_argument("--alerts-out", default=DEFAULT_ALERTS_OUT, help="输出 gov_alerts.json 路径")
    ap.add_argument("--alerts-source-url", default=os.environ.get("ALERTS_SOURCE_URL"), help="可选：远程预警数据源地址（.json/.csv）")
    args = ap.parse_args()
    run(args.source_url, args.out)
    run_alerts(args.alerts_source_url, args.alerts_out)


if __name__ == "__main__":
    main()
