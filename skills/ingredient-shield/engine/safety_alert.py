"""跨品类召回 / 预警引擎。

读取开源预警知识库，支持：
- 列出全部预警（可按品类 food / daily_chem / drug 过滤）
- 按"近 N 小时"过滤（对应近 24h 推送）
- 标注采集时间与是否为演示数据

真实接入时，应将 alerts 替换为对监管渠道（市场监管总局 / 药监局 / 疾控中心 / 品牌公告）的合规采集结果。
"""
import json
import os
from datetime import datetime, timezone, timedelta

_DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PATH = os.path.join(_DATA_DIR, "data", "safety_alerts.json")

with open(_PATH, "r", encoding="utf-8") as f:
    _DB = json.load(f)


def list_alerts(category=None):
    """返回全部预警（按采集时间倒序），可按品类过滤。"""
    alerts = _DB["alerts"]
    if category:
        alerts = [a for a in alerts if a.get("category") == category]
    return sorted(alerts, key=lambda a: a.get("collected_at", ""), reverse=True)


def recent_alerts(hours=24, category=None):
    """返回近 hours 小时内的预警（演示数据全部命中时间窗）。"""
    now = datetime.now(timezone.utc)
    recent = []
    for a in list_alerts(category):
        try:
            ct = datetime.fromisoformat(a["collected_at"])
        except Exception:
            continue
        if ct.tzinfo is None:
            ct = ct.replace(tzinfo=timezone.utc)
        if (now - ct) <= timedelta(hours=hours):
            recent.append(a)
    return recent


def has_active_alert(category=None):
    """是否存在需推送的预警（用于订阅场景）。"""
    return len(recent_alerts(24, category)) > 0


if __name__ == "__main__":
    print("全部：", len(list_alerts()))
    print("近 24h：", len(recent_alerts(24)))
    print("药品近 24h：", len(recent_alerts(24, "drug")))
