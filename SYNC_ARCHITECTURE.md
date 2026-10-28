# 国家公开数据「定期同步」架构说明

> 对应需求：国家公开数据样例从「固定 15 项内嵌样例」升级为「可定期同步、规模可扩展」的真实演示管线；当前内置样例已扩至 **104 项**（食品 42 / 日化 31 / 药品 31）。

## 1. 设计目标与约束

- **零运行时服务器**：站点托管在 GitHub Pages（纯静态），没有任何后端进程、没有可写 API。
- **可扩展**：同步结果不写死在前端，而是由脚本从数据源清洗生成 `gov_products.json`，前端运行时拉取。
- **可回退**：前端拉取失败时回退到内置样例，页面永不空白。
- **合规优先**：只做字段归一化与基础校验，不编造任何官方数据；真实接入需自备授权数据源。

## 2. 数据流

```
[公开公告格式数据源]
       │  (SOURCE_URL 指向你授权的 feed，缺省用内置样例 gov_feed_sample.csv)
       ▼
 sync_gov_data.py  ──复用──▶  GovPublicDataSource (engine/data_source.py)
       │   字段归一化 + 危害规则命中统计 + 写入 _meta.synced_at
       ▼
 gov_products.json  (skills/.../data/  与  docs/  各一份，保持一致)
       │  GitHub Actions 提交回仓库 → Pages 自动重建
       ▼
 前端 index.html  ──运行时 fetch('gov_products.json')──▶  归一化为 GOV_PRODUCTS
       │   失败则回退内嵌样例（15 项）
       ▼
 安全分析卡片：按画像实时标注，并显示「溯源 + 同步时间」
```

## 3. 关键组件

| 文件 | 作用 |
|------|------|
| `skills/ingredient-shield/data/gov_feed_sample.csv` | 公开公告格式样例 feed（列：id,name,category,components,nutrition,contraindications,warnings,source_url,source_type,approved_date,manufacturer）。当前含 104 项（食品 42 / 日化 31 / 药品 31）。 |
| `skills/ingredient-shield/engine/data_source.py` | `GovPublicDataSource`：CSV/JSON 自动识别、按表头归一化、UTF-8 BOM 处理。 |
| `skills/ingredient-shield/engine/sync_gov_data.py` | 同步脚本：读取数据源 → 归一化 → 输出 `gov_products.json`（含 `_meta`：版本、synced_at、分类计数、命中危害规则数、来源说明）。支持 `SOURCE_URL` 环境变量接入远程 feed。 |
| `docs/gov_products.json` | 发布副本，供 Pages 运行时同域拉取。 |
| `docs/index.html` | 前端：启动时 `fetch('gov_products.json')`，归一化为 `GOV_PRODUCTS`，失败回退内嵌样例；切换「国家公开数据」时展示 `synced_at` 与每条溯源。 |
| `.github/workflows/sync-gov-data.yml` | 定时同步：每周一 02:17 UTC + 手动 `workflow_dispatch` + 推送脚本/样例即触发；运行脚本、复制 JSON 到 `docs/`、有变化才提交。 |

## 4. 接入真实授权数据源（可选）

1. 自备一个你**有权使用**的公开公告格式 feed（`.json` 或 `.csv`，字段见上表）。
2. 在仓库 **Settings → Secrets** 增加 `GOV_FEED_URL`，值为该 feed 地址。
3. 手动触发一次 `sync-gov-data` 工作流（或等下个周一），脚本即改用远程 feed 重新生成 `gov_products.json`。

> 未设置 `GOV_FEED_URL` 时，脚本默认使用内置样例，仍保持「定期同步」能力，只是数据源为演示样例。

## 5. 验证方式

- 本地静态服务 `docs/` 后打开页面，切换「国家公开数据」：
  - 分段标签显示「国家公开数据（104 项）」；
  - 备注显示「已同步 104 项 · 更新于 <UTC 时间>（国家公开公告清洗，非官方演示数据）」；
  - 结果卡片含 104 项，且每项带「📄 溯源：来源类型 · 企业 · 日期」。
- 断网 / 拉取失败时：自动回退内嵌 15 项样例，备注提示「内嵌样例 15 项（实时同步暂不可用，已回退到本地样例）」。
- `python3 skills/ingredient-shield/engine/sync_gov_data.py` 本地可独立运行，输出计数与 `synced_at`。

---

## 6. 近期能力升级（匹配精度 A + 跨品类组合风险 E）

为回应"公开数据是否过少"与"分析可优化 / 深化"两点，本轮在**保持「定期同步」架构不变**的前提下，做了三件事：

### 6.1 样例扩容到 104 项
- `gov_feed_sample.csv` 由 36 项扩至 **104 项**（食品 42 / 日化 31 / 药品 31），并补充「否定式成分」（如 无牛奶添加、无麸质）与「组合风险样本」（含酒精、乙醇、水杨酸、服药禁酒等），提升演示可信度与覆盖度。
- 重新生成 `gov_products.json`（skills 与 docs 各一份），`hazard_matched` 约 67 项。

### 6.2 A · 成分匹配精度升级
- **归一化**：去括号注释、去标点/空格、统一小写，避免「全脂牛奶」与「牛奶」匹配不一致。
- **安全子串匹配**：阻断歧义单字键（麦 / 乳 / 鱼），仅放行安全单字键（蛋 / 虾 / 蟹），避免「燕麦」误命中「麦」、「乳酸」误命中「乳」。
- **否定检测**：识别「不含 / 未添加 / 无添加 / free / 无+X」，避免「无牛奶添加」误标含奶。
- **扩充映射**：新增约 30 条成分→危害映射（麸质族、乳制品族、蛋类、甲壳类、坚果、鱼类、维 A 类 / 视黄醇等），危害注册表新增 `retinol`。

### 6.3 E · 跨品类组合风险引擎
- 新增前端 `analyzeCombinations` + 后端镜像 `engine/combination.py`，覆盖三类高风险叠加：
  1. **含酒精产品 + 服药禁酒 / 勿驾驶**（block）；
  2. **水杨酸 / 阿司匹林 内服 + 外用叠加暴露**（warn）；
  3. **孕期画像 + 接触高风险日化物质**（煤焦油 / 视黄醇 / 甲醛释放体）（block）。
- 仅在用户画像命中时触发，不误报未孕用户；组合风险卡独立成节（「⚠ 组合风险预警」），与主分析并列。

> 前端 `index.html` 与 Python 引擎逻辑一致，已用 Playwright 回归验证：104 项样本、子串 / 否定匹配、3 类组合风险、移动端零溢出、拉取失败回退 15 项内嵌样例（全部通过）。
