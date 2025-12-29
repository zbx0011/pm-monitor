# 铂钯跨市场监控系统 - 开发规则

## 日期时间显示规则 ⚠️ 重要

在修改 `precious_metals_monitor.html` 时，**除非用户明确要求**，否则不得修改以下日期时间显示逻辑：

### 1. 价差排行榜时间
- 每行显示该配对的**价格对应时间**
- 时间来源：`pair.history` 数组最后一条的 `date` 字段
- 不是 `update_time`，不是当前时间

### 2. 历史价差走势图时间
- 使用对应JSON数据文件中的时间字段

### 3. 验证清单
修改前请确认：
- [ ] 是否涉及时间显示？如果是，用户是否明确要求修改？
- [ ] 时间来源是否正确（价格时间 vs 更新时间 vs 当前时间）？
- [ ] 广期所和CME显示的是同一匹配时间点？

## 数据源规则

| 品种 | 排行榜数据源 | 图表数据源 |
|------|-------------|-----------|
| 铂金 | platinum_all_pairs.json | platinum_all_pairs.json |
| 钯金 | palladium_all_pairs.json | palladium_all_pairs.json |
| 黄金 | contract_convergence_data.json | contract_convergence_data.json |
| 白银 | contract_convergence_data.json | contract_convergence_data.json |

## 下拉选项同步规则

当数据文件中的配对数量变化时，需要同步更新HTML中的 `<select>` 选项：
- `#platinum-pair-select` 铂金配对
- `#palladium-pair-select` 钯金配对
- `#gold-pair-select` 黄金合约
- `#silver-pair-select` 白银合约
