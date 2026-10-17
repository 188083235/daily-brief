# daily-brief 每日简报

每天 100 条按重要程度排序的中文简报（原文来自中/英/韩/日等原语种主流来源 + 个人订阅源），约 10% 为「探索位」。

- `index.html` 今日；`archive/` 往期；`data/issue-YYYY-MM-DD.json` 结构化数据
- 交互：默认只显示标题；点标题→摘要+看点（depth 1=感兴趣）；再点「展开详细」/摘要→长文+原文链接（depth 2=很感兴趣）；未打开=不感兴趣。记录每条最大深度、时间戳、是否点原文、可选备注（localStorage，按天），页底一键复制反馈 JSON
- 信源清单：私有，不在公开仓库中（本地 `sources/channels.json`）；公开的主流补充源见 `pipeline/supplement_sources.py`
- 流水线：`./run_daily.sh YYYY-MM-DD` → collect（抓取/去重/聚类/打分）→ select（配额+探索位、解析原文链接、抓正文）→ editorial（据正文写中文标题 t / 摘要 s / 看点 w / 详细 detail，detail 写在 DETAIL[cid]，3–6 段，只依据抓到的原文）→ build_issue（校验每条都有原文依据）→ render
- 原则：只用真实来源，不编造；无原文正文支撑的条目会被丢弃。

## 固定关注（fixed topics）

- 页面顶部「📌 固定关注」区：每个主题列出过去 72 小时的相关报道（只用实际抓到的正文；没有新报道就写明）。
- 「⚙ 设置」面板：增删主题，别名用 / 分隔（如 `당진/唐津/Dangjin`）。修改保存在浏览器本地（`localStorage: daily-brief:fixed-topics`）；「提交到 GitHub」会打开预填的 new-issue 页面（标题 `config: fixed-topics`，标签 `config`，正文含 JSON）。
- 流水线 `pipeline/fixed_topics.py` 每次运行前用 GH_TOKEN 读取**仓库主人**提交的最新一条 `config: fixed-topics` issue（open 或 closed 均可），否则回退到 `config/fixed_topics.json`。其他人提交的 issue 会被忽略。
- 检索来源：Google News（中文简/繁、韩文、英文查询）、当地媒体 RSS（如当津시대）。Naver 新闻只通过官方 Search API，需设置 `NAVER_CLIENT_ID` / `NAVER_CLIENT_SECRET`，未设置则跳过。
- 「唐津」会排除日本佐贺县唐津市（Karatsu）的报道。

## 排序

用户自己的 RSS/收藏源在打分时有小幅加权（+0.6，或簇内含用户源 +0.3），各类别配额不变，不会挤掉覆盖面。来源归属（user/added）只写到本地未跟踪的 `data/origin-stats-*.json`，不进入公开数据。

## 每日反馈

- 页面底部「提交反馈到 GitHub ↗」打开预填 issue（标题 `feedback: YYYY-MM-DD`），正文为紧凑 JSON：只含打开过/点过原文/写了备注的条目、统计和分类计数。URL 超过约 7800 字符时依次去掉标题、分类统计、截断备注、省略最浅的记录，并在 JSON 的 `trimmed` 字段和页面状态里注明；完整版仍可用「一键复制反馈 JSON」。本机记录是否已打开过提交页、之后是否有新记录。
- `pipeline/feedback.py fetch` 用 GH_TOKEN 读取**仓库主人**的 `feedback:` issue，存到 `data/feedback/`（未跟踪）。`propose` 生成偏好调整建议（`prefs-proposed.json`，不生效）；只有用户同意后运行 `approve` 写出的 `prefs-approved.json` 才会被 `collect.py` 使用（分类分数 ±0.5 以内）。`weekly` 生成每周小结。

## 设置与反馈（合并提交）

页面底部「⚙ 设置与反馈」面板合并了固定关注设置和今日反馈，一个「提交到 GitHub ↗」按钮打开预填 issue `update: YYYY-MM-DD`，正文 JSON 为 `{"v":2,"type":"update","date":…,"feedback":{…},"fixed_topics":{"topics":[…]}}`（`fixed_topics` 仅在本机修改过时附带）。JSON 默认折叠（「查看 JSON」）。`fixed_topics.py` 与 `feedback.py` 同时兼容旧标题 `config: fixed-topics` / `feedback:`，都只接受仓库主人提交的 issue。

同一天重新生成时，旧版本保存在 `data/versions/issue-DATE-vN.json` 并渲染为 `archive/DATE-vN.html`；`collect.py --end now` 可让窗口截止到当前时间。
