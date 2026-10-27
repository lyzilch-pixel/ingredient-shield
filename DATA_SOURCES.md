# 可插拔数据源接入说明

本文件说明成分避雷如何获取数据，以及如何从演示用的本地知识库切换到真实数据源。

> ⚠️ 成分避雷**不绑定任何单一品牌或单一 MCP**。旧版（麦安溯源）仅依赖麦当劳 MCP，本版已彻底解耦：产品数据通过统一接口 `list_products()` 提供，来源可自由替换。

---

## 一、数据源抽象

所有数据源都只需实现两个方法，即可被引擎无缝使用：

```python
class DataSource:
    def list_products(self, category=None) -> list[dict]:
        """返回产品清单；category 可为 food / daily_chem / drug。"""
    def get_product(self, pid) -> dict | None:
        """按 id 返回单个产品。"""
```

每个产品统一字段：
- `id`, `name`, `category`（food / daily_chem / drug）
- `components`：成分 / 配料 / 活性物质列表
- 食品额外带 `nutrition` 字典；药品额外带 `contraindications`（健康禁忌 id 列表）与 `warnings`
- 可选 `provenance` 关联键

---

## 二、当前默认：本地演示库

`skills/ingredient-shield/data/products.json` 内置常见食品、日化个护、药品的示例数据，无需任何 Token 即可运行：

```python
from engine.data_source import get_client
client = get_client("local")          # 本地演示库
foods = client.list_products("food")
drugs = client.list_products("drug")
```

---

## 三、接入真实数据源（可插拔示例）

真实接入时，在 `engine/data_source.py` 的工厂 `get_client()` 中新增分支即可，引擎与前端无需改动。

### 1. 食品成分库（公开数据源）
- 开放食品数据库（如 Open Food Facts 类公开 API）
- 对接方式：实现 `OpenFoodDataSource.list_products()`，将外部返回映射为统一产品结构（含 `nutrition`）。

### 2. 日化成分数据库
- 化妆品成分安全资料库（如公开 INCI / EWG 类数据源）
- 对接方式：实现 `CosmeticDBSource`，将成分名映射到 `components.json` 的致敏原 / 风险物质 id。

### 3. 药品说明书库
- 药品说明书 / 合理用药数据源（如公开药品数据库）
- 对接方式：实现 `DrugLabelSource`，抽取 `contraindications` 与成分过敏原。

### 4. 跨品类召回 / 预警源
- 国家市场监管总局、药监局、疾控中心及品牌官方公告
- 对接方式：将权威发布归一化为 `safety_alerts.json` 结构（含 `category` / `collected_at`）。

---

## 四、替换示例（伪代码）

```python
def get_client(mode="local"):
    if mode == "local":
        return LocalDataSource()
    if mode == "openfood":
        return OpenFoodDataSource(api_key=os.environ.get("OPENFOOD_KEY"))
    if mode == "druglabel":
        return DrugLabelSource()
    raise ValueError(f"未知数据源模式：{mode}")
```

---

## 五、合规边界

- 真实数据源需遵守对方服务条款与 robots/API 限流，禁止违规爬取。
- 任何源自第三方的数据都应在前端标注"数据来源"与"采集时间"，并保留非官方免责声明。
- 个人安全画像仅存本地 / 本会话，不上传任何数据源。

---

> 旧版依赖的麦当劳 MCP 已不再使用；如仅作历史参考，原 `mcd-mcp-server` 相关说明已自本仓库移除。
