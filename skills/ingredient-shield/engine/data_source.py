"""可插拔数据源客户端（取代旧的麦当劳 MCP 客户端）。

设计原则：成分避雷不绑定任何单一品牌或单一 MCP。数据源通过统一接口提供
"产品清单"，具体来源可插拔：
- LocalDataSource：读取 data/products.json，用于 Demo 与单元测试，无需任何 Token。
- GovPublicDataSource：读取 data/gov_products.json/csv，模拟从国家公开公告（NMPA药品/化妆品备案、
  市场监管食品抽检/召回、食品生产许可等）清洗后的结构化数据。
- 真实接入时，可新增 OpenFoodDataSource / CosmeticDBSource / DrugLabelSource 等，
  只要实现 list_products() / get_product() 即可无缝替换。

接口对齐产品库结构：products 含 category（food / daily_chem / drug）等字段。
"""
import json
import csv
import os.path as _p
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

_DATA_DIR = _p.dirname(_p.dirname(_p.abspath(__file__)))


def _load_local():
    with open(_p.join(_DATA_DIR, "data", "products.json"), "r", encoding="utf-8") as f:
        return json.load(f)


class BaseDataSource(ABC):
    """数据源抽象基类：所有可插拔源需实现此接口。"""

    @abstractmethod
    def list_products(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """返回产品列表，可按 category 过滤。"""

    @abstractmethod
    def get_product(self, pid: str) -> Optional[Dict[str, Any]]:
        """按 ID 取单条产品，不存在返回 None。"""


class LocalDataSource(BaseDataSource):
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


class GovPublicDataSource(BaseDataSource):
    """政府公开公告清洗后的结构化数据源（JSON 或 CSV）。

    预期字段映射（最小集）：
    - id: 唯一标识（如：food_001 / drug_001 / chem_001）
    - name: 商品名
    - category: food | daily_chem | drug
    - components: 成分列表（JSON 数组字符串或 ; 分隔）
    - nutrition: 食品营养（JSON 字符串，可选）
    - contraindications: 药品禁忌（JSON 数组字符串或 ; 分隔，可选）
    - warnings: 警示语（可选）
    - source_url: 溯源链接（公开公告页/备案页，合规必需）
    - source_type: 来源类型（如：nmpa_drug / nmpa_cosmetic / samr_food_recall / food_license）
    - approved_date: 批准/公告日期（可选）
    - manufacturer: 生产企业（可选）
    """

    def __init__(self, path: Optional[str] = None):
        if path is None:
            path = _p.join(_DATA_DIR, "data", "gov_products.json")
        self._path = path
        self._products: List[Dict[str, Any]] = []
        self._index: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        ext = _p.splitext(self._path)[1].lower()
        if ext == ".json":
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            products = data.get("products", []) if isinstance(data, dict) else data
        elif ext == ".csv":
            products = []
            with open(self._path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    products.append(self._normalize_row(row))
        else:
            raise ValueError(f"不支持的文件格式：{ext}，仅支持 .json 或 .csv")

        self._products = products
        self._index = {p["id"]: p for p in products if "id" in p}

    def _normalize_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """将 CSV 行归一化为标准 Product 结构。"""
        # components / contraindications 支持 ; 或 JSON 数组
        def parse_list(v: Optional[str]) -> List[str]:
            if not v:
                return []
            v = str(v).strip()
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [x.strip() for x in v.split(";") if x.strip()]

        def parse_json(v: Optional[str]) -> Optional[Dict]:
            if not v:
                return None
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None

        def safe_strip(v: Optional[str]) -> Optional[str]:
            if v is None:
                return None
            s = str(v).strip()
            return s if s else None

        return {
            "id": safe_strip(row.get("id")),
            "name": safe_strip(row.get("name")),
            "category": safe_strip(row.get("category")),
            "components": parse_list(row.get("components")),
            "nutrition": parse_json(row.get("nutrition")),
            "contraindications": parse_list(row.get("contraindications")),
            "warnings": safe_strip(row.get("warnings")),
            "source_url": safe_strip(row.get("source_url")),
            "source_type": safe_strip(row.get("source_type")),
            "approved_date": safe_strip(row.get("approved_date")),
            "manufacturer": safe_strip(row.get("manufacturer")),
        }

    def list_products(self, category=None):
        items = self._products
        if category:
            return [p for p in items if p.get("category") == category]
        return items

    def get_product(self, pid):
        return self._index.get(pid)


def get_client(mode="local", **kwargs):
    """数据源工厂。

    mode:
    - "local": LocalDataSource（默认，内置演示数据）
    - "gov": GovPublicDataSource（读取 data/gov_products.json 或 .csv）
      可通过 path=... 指定自定义路径
    """
    if mode == "local":
        return LocalDataSource()
    if mode == "gov":
        return GovPublicDataSource(kwargs.get("path"))
    raise ValueError(f"未知数据源模式：{mode}（支持：local, gov）")


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "local"
    c = get_client(mode)
    print(f"[{mode}] 食品：{len(c.list_products('food'))}  日化：{len(c.list_products('daily_chem'))}  药品：{len(c.list_products('drug'))}")
    # 简单验证
    for cat in ("food", "daily_chem", "drug"):
        items = c.list_products(cat)
        if items:
            print(f"  首条 {cat}：{items[0]['name']} (id={items[0]['id']})")
