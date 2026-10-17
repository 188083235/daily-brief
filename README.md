# daily-brief 每日简报

每天 100 条按重要程度排序的中文简报（原文来自中/英/韩/日等原语种主流来源 + 个人订阅源），约 10% 为「探索位」。

- `index.html` 今日；`archive/` 往期；`data/issue-YYYY-MM-DD.json` 结构化数据
- 反馈按钮（有用/没用/多来点/备注）存于浏览器 localStorage，页底可一键复制当天反馈 JSON
- 信源清单：私有，不在公开仓库中（本地 `sources/channels.json`）；公开的主流补充源见 `pipeline/supplement_sources.py`
- 流水线：`./run_daily.sh YYYY-MM-DD` → collect（抓取/去重/聚类/打分）→ select（配额+探索位、解析原文链接、抓正文）→ editorial（据正文写中文标题/摘要/看点）→ build_issue（校验每条都有原文依据）→ render
- 原则：只用真实来源，不编造；无原文正文支撑的条目会被丢弃。
