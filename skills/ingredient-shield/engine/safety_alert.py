"""跨品类召回 / 预警引擎（J：真实预警同步 + 兜底演示数据）。

读取同步管线产出的 gov_alerts.json（若存在），否则兜底读取本地演示 safety_alerts.json。
支持：
- 列出全部预警（可按品类 food / daily_chem / drug 过滤）
- 按"近 N 小时"过滤（对应近 24h 推送）
- 标注采集时间、是否为演示数据、同步时间（来自 gov_alerts.json._meta.synced_at）

真实接入时，应配置 ALERTS_SOURCE_URL 定期同步监管渠道（市场监管总局 / 药监局 / 疾控中心 / 品牌公告）的合规采集结果。
"""
import json
import os
from datetime import datetime, timezone, timedelta

_DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SYNCED_PATH = os.path.join(_DATA_DIR, "data", "gov_alerts.json")
_FALLBACK_PATH = os.path.join(_DATA_DIR, "data", "safety_alerts.json")


def _load_alerts():
    """优先读取同步产出的 gov_alerts.json，否则兜底 safety_alerts.json。"""
    # 1) 尝试读取同步后的文件
    if os.path.exists(_SYNCED_PATH):
        try:
            with open(_SYNCED_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            alerts = data.get("alerts", [])
            meta = data.get("_meta", {})
            return alerts, {"source": "synced", "synced_at": meta.get("synced_at"), "version": meta.get("version")}
        except Exception:
            pass
    # 2) 兜底：本地演示数据
    try:
        with open(_FALLBACK_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        alerts = data.get("alerts", [])
        return alerts, {"source": "fallback", "synced_at": None, "version": data.get("_meta", {}).get("version")}
    except FileNotFoundError:
        return [], {"source": "none", "synced_at": None, "version": None}


_ALERTS, _META = _load_alerts()


def get_meta():
    """返回数据源元信息（供前端展示同步时间/来源）。"""
    return _META


def list_alerts(category=None):
    """返回全部预警（按采集时间倒序），可按品类过滤。"""
    alerts = _ALERTS
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
    print("数据源：", _META)
