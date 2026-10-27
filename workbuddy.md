# 开发实录 · workbuddy.md

> 本文件记录使用 WorkBuddy 完成的开发过程，作为项目开发留痕。

---

## 开发环境

- 工具：WorkBuddy（专家「产品憨憨」）
- 语言：Python 3（核心引擎）+ 纯 HTML/JS（前端）
- 模式：本地可插拔演示库，无需任何 Token

---

## 开发时间线（节选）

### 阶段 1：范围重定义（由单品牌 → 跨品类）
- 原项目「麦安溯源」深度绑定麦当劳 MCP。经核实，麦当劳 MCP 专项（麦当劳程序员创意开发大赛）官方规则**强制要求**"基于麦当劳 MCP 能力开发"，报名/排名截止 2026-10-26 前已收口。
- 决策：彻底去麦当劳化，将项目重做为一个通用的**跨品类消费品安全决策引擎**，命名为**成分避雷（IngredientShield）**，覆盖食品 / 日化个护 / 药品。
- 删除麦当劳专属文件：`MCP_INTEGRATION.md`、`CONTEST_DECLARATION.md`、`mcp-config.example.json` 及 `allergen_db.py`、`mcp_client.py`、`traceability.py` 等。

### 阶段 2：统一危害注册表设计
- `components.json`：跨品类危害注册表，含食品过敏原（14 类）、日化致敏原/风险物质、药品过敏、健康禁忌（条件）四类。
- `component_db.py`：成分→危害映射 + 交叉污染"可能含" + 用户画像命中判定（品类无关）。

### 阶段 3：品类分析器
- `nutrition.py`：食品营养风险（沿用膳食指南单份占比阈值）。
- `product_safety.py`：日化风险物质分级（甲醛释放体/煤焦油 high，其余 warn）。
- `drug_safety.py`：药品健康禁忌（条件）+ 成分过敏（青霉素/阿司匹林/磺胺）双重校验。
- `provenance.py`：溯源/资质（由食材溯源泛化）。
- `safety_alert.py`：跨品类召回预警（新增 category 维度）。
- `profile.py`：跨品类个人安全画像（危害 id + 健康状态 + 营养约束）。

### 阶段 4：编排与数据源解耦
- `rules.py`：跨品类 `evaluate_item` / `recommend_for_profile` / `build_safety_list`，统一输出 safe/warn/block。
- `data_source.py`：可插拔数据源（取代旧的单一品牌 MCP 客户端），默认本地 `products.json`，真实源可替换。

### 阶段 5：CLI 演示验证
- `demo.py` 验证 5 个跨品类用户故事（US-1 ~ US-5）全部跑通：
  - US-1 食品过敏（花生+麸质）→ 安全 5 / 排除 5
  - US-2 日化敏感（MIT+香精）→ 命中全部相关日化
  - US-3 孕期 → 排除布洛芬/甲硝唑，其余可服
  - US-4 跨品类近 24h 预警
  - US-5 跨品类"我的安全消费清单"

### 阶段 6：前端与文档
- `frontend/index.html`：纯前端跨品类页面（食品/日化/药品 Tab + 跨品类画像 + 分享卡）。
- 文档：README / SKILL / DATA_SOURCES / DISCLAIMER / 产品提案。

---

## 关键工程决策

1. **彻底去品牌化**：移除所有"麦当劳/MCP/非官方麦当劳数据"耦合，引擎改为品类无关。
2. **统一危害抽象**：食品过敏原、日化致敏原、药品过敏统一进 `components.json`，避免多套映射。
3. **数据源可插拔**：以 `list_products()` 统一接口解耦，演示库与真实源可互换。
4. **端到端一致性**：前端 JS 引擎与 Python 引擎对核心逻辑保持一致（Demo 已比对）。

---

## 验证记录

| 项 | 命令 / 方式 | 结果 |
|----|-----------|------|
| CLI 5 用户故事 | `python demo.py` | ✅ 全部通过 |
| 跨品类召回 | `safety_alert.recent_alerts(24)` | ✅ 按品类过滤正常 |
| 引擎自测 | 各子模块 `__main__` | ✅ OK |

---

## 已知限制（诚实降级）

- 危害映射基于关键字推导，真实产品需重新抽样校验。
- 溯源 / 召回 / 药品数据为示例知识库，需接入权威渠道替换。
- 健康禁忌校验基于说明书共识，重症状况须遵医嘱。

---

> 本实录由 WorkBuddy 生成，记录成分避雷（IngredientShield）的开发过程。
