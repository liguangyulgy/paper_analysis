# AGENTS.md

## 项目定位

本项目用于持续跟踪、整理和分析 genOway / 基锘威相关动物模型应用论文。

目标不是简单下载论文，而是建立一个可持续维护的文献情报库，能够回答：

- 哪些论文使用了相关动物模型；
- 涉及哪些疾病领域、靶点和应用场景；
- 是否明确提到 genOway / 基锘威；
- 论文是否有市场、销售、产品规划参考价值；
- 哪些论文需要人工审核或手动补充全文；
- 在中国境内有哪些机构、课题组或论文线索涉及相关模型应用。

## 重要边界

必须遵守以下规则：

1. 不把 genOway 官网作为数据源。
2. 不自动批量爬取 Google Scholar。
3. 不绕过出版社付费墙。
4. 不使用 Sci-Hub 等非正规来源。
5. 只自动下载合法开放获取 PDF / XML / HTML 全文。
6. 用户手动提供的 PDF 可以分析，但必须标记 `manual_upload = true`。
7. Google Scholar Alerts 邮件只作为发现线索，不作为正式证据。
8. Google Scholar Web 链接只作为人工跳转入口，不后台自动点击或下载。
9. 中文数据库，如 CNKI、万方、维普、SinoMed、NSTL，第一版只做人工检索入口和题录/全文手动导入。
10. CAJ 文件第一版只登记为 `conversion_needed`，不直接解析。
11. 所有自动分析结果默认可被人工修订。
12. 人工确认过的字段不得被后续自动任务覆盖。

## 优先实现顺序

第一阶段优先完成：

1. SQLite 数据库；
2. PubMed 摘要获取；
3. Crossref DOI 补全；
4. Unpaywall 开放全文发现；
5. 手动 PDF 导入；
6. PDF 文本解析；
7. 证据句抽取；
8. 论文状态维护；
9. Excel / Markdown 报告导出；
10. CLI 手动运行接口。

第二阶段完成：

1. Streamlit WebUI 审核工作台；
2. 论文详情页外部链接入口；
3. 手动 PDF 上传和状态更新；
4. 高价值候选、待审核、全文缺失等队列；
5. 报告下载入口。

第三阶段再补：

1. Europe PMC 全文 XML；
2. OpenAlex；
3. Semantic Scholar；
4. Google Scholar Alerts 邮件导入；
5. 中文数据库检索入口；
6. CAJ 上传登记；
7. GROBID；
8. 趋势分析和机构分析。

## 编码要求

- 使用 Python。
- 第一版使用 SQLite。
- 所有网络请求必须支持限速、重试、日志和缓存。
- 所有数据采集模块必须支持增量运行。
- 所有状态变更必须写入数据库。
- 所有命令必须可以通过 CLI 手动触发。
- 所有 WebUI 修改必须复用 repository 层，不允许页面代码直接拼 SQL。
- 所有自动判断字段都应允许人工覆盖。
- 所有 LLM 或规则抽取结果必须带证据句。
- 关键逻辑需要单元测试。

## 推荐工程结构

```text
paper_analysis/
  README.md
  AGENTS.md
  pyproject.toml
  .env.example

  configs/
    queries.yaml
    model_keywords.yaml
    chinese_queries.yaml
    disease_taxonomy.yaml
    application_taxonomy.yaml
    report_config.yaml

  data/
    raw/
      pdf/
      xml/
      html/
      manual_uploads/
      scholar_alerts/
      chinese_records/
    processed/
    exports/

  docs/

  src/
    cli.py
    webui/
      streamlit_app.py
      pages/
      components/
    collectors/
    fulltext/
    parsers/
    analysis/
    reports/
    storage/
    utils/

  tests/
```
