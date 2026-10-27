"""可插拔数据源客户端（取代旧的麦当劳 MCP 客户端）。

设计原则：成分避雷不绑定任何单一品牌或单一 MCP。数据源通过统一接口提供
"产品清单"，具体来源可插拔：
- LocalDataSource：读取 data/products.json，用于 Demo 与单元测试，无需任何 Token。
- 真实接入时，可新增 OpenFoodDataSource / CosmeticDBSource / DrugLabelSource 等，
  只要实现 list_products() / get_product() 即可无缝替换。

接口对齐产品库结构：products 含 category（food / daily_chem / drug）等字段。
"""
import json
import os.path as _p

_DATA_DIR = _p.dirname(_p.dirname(_p.abspath(__file__)))


def _load_local():
    with open(_p.join(_DATA_DIR, "data", "products.json"), "r", encoding="utf-8") as f:
        return json.load(f)


class LocalDataSource:
    """本地多品类产品库（演示 / 测试）。"""

    def __init__(self):
        self._data = _load_local()

    def list_products(self, category=None):
        items = self._data["products"]
        if category:
            return [p for p in items if p.get("category") == category]
        return items

    def get_product(self, pid):
        for p in self._data["products"]:
            if p.get("id") == pid:
                return p
        return None


def get_client(mode="local"):
    """数据源工厂。当前仅 local；扩展时在此接入其余可插拔源。"""
    if mode == "local":
        return LocalDataSource()
    raise ValueError(f"未知数据源模式：{mode}（当前仅支持 local）")


if __name__ == "__main__":
    c = get_client("local")
    print("食品：", len(c.list_products("food")))
    print("日化：", len(c.list_products("daily_chem")))
    print("药品：", len(c.list_products("drug")))
