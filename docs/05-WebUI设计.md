# 05-WebUI设计

## 1. 定位

WebUI 是文献审核工作台，不替代 CLI。

CLI 负责：

- 批量采集；
- 去重；
- 全文发现；
- PDF/XML 解析；
- 自动分析；
- 报告生成。

WebUI 负责：

- 人工审核；
- 论文状态维护；
- 外部链接跳转；
- PDF 上传；
- 证据句查看；
- 报告下载；
- 中文数据源人工检索入口。

第一版推荐使用 Streamlit，不做复杂权限系统。

## 2. 总体页面

建议页面包括：

```text
Dashboard 首页
论文列表
论文详情
手动上传
报告中心
中文数据源
系统状态
```

## 3. Dashboard 首页

展示整体状态：

- 总论文数；
- 已获取摘要数量；
- 已获取全文数量；
- 待审核数量；
- 高价值候选数量；
- 已确认高价值数量；
- 全文受限数量；
- 解析失败数量；
- CAJ 待转换数量；
- 中国境内应用线索数量；
- 本周新增数量。

快捷入口：

- 查看待审核；
- 查看高价值候选；
- 查看全文缺失；
- 查看中国境内线索；
- 上传 PDF；
- 导出本周报告。

## 4. 论文列表页

支持筛选：

- 关键词；
- 年份；
- 期刊；
- 语言；
- 来源；
- 模型；
- 疾病领域；
- evidence_level；
- reference_value；
- abstract_status；
- fulltext_status；
- review_status；
- region_relevance；
- manual_upload；
- manual_override。

列表字段：

- 标题；
- 年份；
- 期刊；
- 模型；
- 疾病领域；
- 证据等级；
- 参考价值；
- 全文状态；
- 审核状态；
- 中国境内相关性；
- 最后更新时间。

## 5. 论文详情页

论文详情页是核心页面。

### 5.1 基础信息区

显示：

- title；
- authors；
- journal；
- year；
- DOI；
- PMID；
- PMCID；
- source；
- abstract；
- language；
- region_relevance。

### 5.2 状态与人工操作区

显示并允许修改：

- evidence_level；
- reference_value；
- review_status；
- region_relevance；
- model_name；
- model_type；
- target；
- disease_area；
- application_scenario；
- note。

保存人工修改时必须设置：

```text
manual_override = true
```

### 5.3 证据句区

展示：

- 证据句；
- 所在章节；
- 抽取字段；
- confidence_score；
- needs_review；
- 来源：摘要 / PDF / XML / 手动全文。

没有证据句的自动结论不能进入高价值报告。

### 5.4 原文获取区

每篇论文显示外部链接按钮：

- DOI 页面；
- PubMed 页面；
- PMC 全文；
- Unpaywall OA 页面；
- Unpaywall PDF；
- Semantic Scholar 页面；
- Semantic Scholar PDF；
- OpenAlex 页面；
- Google Scholar 检索；
- 出版社页面；
- CNKI 检索；
- 万方检索；
- 维普检索；
- SinoMed 检索；
- NSTL 检索；
- 上传我已下载的 PDF。

Google Scholar 只作为人工跳转入口，不允许后台自动爬取或批量下载。

### 5.5 PDF / 全文预览区

支持：

- 显示已解析文本；
- 搜索 genOway、基锘威、模型名、靶点、疾病词；
- 展示 Methods、Funding、Conflict of Interest 等关键章节；
- 提供上传新版本 PDF 的入口。

## 6. 手动上传页

支持上传：

- PDF；
- TXT；
- MD；
- CAJ。

PDF / TXT / MD 上传后进入解析流程。

CAJ 上传后只登记，不解析，并提示：

```text
该文件为 CAJ 格式，系统暂不直接解析。
请使用 CAJViewer 等本地工具转换为 PDF 后重新上传。
```

上传时可以指定：

- paper_id；
- DOI；
- PMID；
- title；
- source；
- 是否中文论文；
- 是否中国境内应用线索。

## 7. 中文数据源页

提供人工检索入口：

- CNKI；
- 万方；
- 维普；
- SinoMed；
- NSTL。

功能：

- 选择关键词；
- 生成检索 URL；
- 打开外部数据库；
- 手动录入中文论文；
- 上传中文 PDF / CAJ；
- 导入题录 CSV。

## 8. 报告中心

支持导出：

- 周报；
- 月报；
- 高价值论文报告；
- 待审核报告；
- 模型应用报告；
- 疾病领域报告；
- 中国境内应用线索报告；
- 全文缺失报告；
- CAJ 待转换报告。

格式：

- Excel；
- Markdown；
- CSV。

## 9. WebUI 工程要求

- 所有 WebUI 修改必须通过 repository 层写数据库；
- 页面代码不直接拼 SQL；
- 所有人工修改写入 manual_notes；
- 所有人工修改设置 manual_override；
- 外部链接生成逻辑放在 `fulltext/link_builder.py`；
- WebUI 不执行长时间批处理任务，只触发 CLI 或后台任务入口；
- 第一版不做复杂权限系统。
