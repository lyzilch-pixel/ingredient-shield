"""成分避雷核心引擎包（跨品类消费品安全决策引擎）。

子模块：
- component_db: 统一危害注册表与成分→危害映射（食品过敏原 / 日化致敏原 / 药品过敏 / 健康禁忌）
- nutrition: 食品营养风险分析（仅食品品类）
- product_safety: 日化个护风险物质分析（仅日化品类）
- drug_safety: 药品禁忌 / 成分过敏分析（仅药品品类）
- provenance: 产品溯源 / 资质
- safety_alert: 跨品类召回 / 预警
- profile: 跨品类个人安全画像
- data_source: 可插拔数据源（取代旧的单一品牌 MCP 客户端）
- rules: 规则编排（对外主入口）
"""
__version__ = "2.0.0"
