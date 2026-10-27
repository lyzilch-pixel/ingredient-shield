# 公开公告 → 标准化字段 清洗规则表

> 本文档说明 `engine/data_source.py` 中 `GovPublicDataSource` 如何把"国家公开公告"
> （NMPA 药品/化妆品备案、市场监管食品抽检/召回、食品生产许可等）清洗为成分避雷
> 统一产品 schema。它是**演示级**清洗管线，真实接入时每个来源需按其官方导出格式微调。

## 1. 目标 schema（最小字段集）

| 字段 | 类型 | 说明 | 是否必填 |
|------|------|------|----------|
| `id` | string | 唯一标识，建议 `<来源前缀>_<序号>`（如 `food_001`/`drug_001`/`chem_001`） | 必填 |
| `name` | string | 商品名 | 必填 |
| `category` | enum | `food` / `daily_chem` / `drug` | 必填 |
| `components` | list[string] | 成分列表（JSON 数组字符串或 `;` 分隔） | 必填 |
| `nutrition` | object | 食品营养（JSON 字符串，可选） | 食品可选 |
| `contraindications` | list[string] | 药品禁忌（JSON 数组或 `;` 分隔，可选） | 药品可选 |
| `warnings` | string | 警示语（可选） | 可选 |
| `source_url` | string | 溯源链接（公开公告页/备案页，**合规必需**） | 强烈建议 |
| `source_type` | enum | 来源类型（见下表） | 建议 |
| `approved_date` | string | 批准/公告日期 `YYYY-MM-DD` | 可选 |
| `manufacturer` | string | 生产企业 | 可选 |

### 来源类型枚举（`source_type`）

| 值 | 含义 |
|----|------|
| `food_license` | 食品生产许可（SC 证）公示 |
| `samr_food_recall` | 市场监管总局 食品抽检/召回公告 |
| `nmpa_drug` | 国家药监局 药品注册/说明书 |
| `nmpa_cosmetic` | 国家药监局 化妆品备案/注册 |

## 2. 字段映射（公告原文 → 标准字段）

| 公告原文常见字段 | 标准字段 | 备注 |
|------------------|----------|------|
| 产品名称 / 品名 | `name` | 去空格、去冗余后缀 |
| 类别 / 产品分类 | `category` | 需映射到本引擎三分类 |
| 成分 / 配料表 / 全成分 | `components` | 中文逗号、顿号、`;` 统一切分为数组 |
| 营养成分表 | `nutrition` | 仅食品；保留 `calories/protein/fat/carbs/sodium/sugar/trans_fat` |
| 禁忌 / 禁用人群 / 注意事项 | `contraindications` + `warnings` | 关键词映射到条件 id（见 §4） |
| 备案号 / 公告链接 | `source_url` | 必须保留，用于溯源 |
| 生产企业 | `manufacturer` | 原样保留 |
| 批准日期 / 公告日期 | `approved_date` | 归一为 `YYYY-MM-DD` |

## 3. 已处理的脏数据边角（实现已覆盖）

| 问题 | 触发场景 | 处理 |
|------|----------|------|
| UTF-8 BOM | CSV 首列键变为 `\ufeffid` | 读取用 `encoding='utf-8-sig'` |
| JSON 字段内含逗号 | `nutrition` 写成 `{calories:250,...}` 被 CSV 拆分 | 整段 JSON 用双引号包裹为单一列 |
| 可选字段为空 | 日化行无 `nutrition`、药品无 `components` 营养 | 空单元格归一为空数组/空对象/`null` |
| `;` 与 JSON 数组混用 | 不同来源导出格式不一致 | `parse_list` 先判 `[` 再 JSON 解析，否则按 `;` 切分 |
| 字符串首尾空格 | 公告复制带入空白 | `safe_strip` 统一去空格，空串归 `null` |

## 4. 禁忌关键词 → 条件 id 映射（药品）

| 公告原文关键词 | 条件 id | 中文 |
|----------------|---------|------|
| 孕妇 / 妊娠 / 哺乳期 | `pregnancy` / `lactation` | 孕期 / 哺乳期 |
| 慎用 / 禁用于肾功能不全 | `kidney` | 肾功能不全 |
| 未成年人禁用 / 18 岁以下 | `minors` | 未成年人 |
| 服药期间禁酒 / 忌酒 | `alcohol` | 服药禁酒 |
| 服药勿驾驶 / 可能引起嗜睡 | `driving` | 服药勿驾驶 |
| 高血压慎用 | `hypertension` | 高血压 |

## 5. 真实接入建议

- **食品**：可用国家食品安全抽检公布数据、食品生产许可 SC 证公示，按 `food_license` / `samr_food_recall` 标注。
- **日化**：NMPA 化妆品备案/注册信息（全成分公示），按 `nmpa_cosmetic` 标注；风险物质再经 `product_safety.py` 的 `HIGH_SUBSTANCES` 判定。
- **药品**：NMPA 药品说明书（核准）中的【禁忌】【注意事项】，映射到条件 id。
- 每个来源建议单独写一个 `BaseDataSource` 子类（如 `OpenFoodDataSource` / `CosmeticDBSource` / `DrugLabelSource`），实现 `list_products()` / `get_product()` 即可无缝替换，前端通过 `get_client(mode=...)` 切换。

> ⚠️ 本文件与示例数据均为**演示用途**，链接与生产企业为占位示例，未指向真实官方记录。
