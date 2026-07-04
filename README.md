# paper_analysis 项目文档

本项目用于持续跟踪、整理和分析 genOway / 基锘威动物模型相关论文，重点支持：

- 自动获取论文信息及摘要；
- 自动寻找合法开放全文并分析；
- 分析用户手动整理的论文全文；
- 通过 WebUI 辅助人工审核、跳转外部文献入口、上传 PDF；
- 支持中国境内应用情况研究，包括中文数据源线索、中文 PDF、CAJ 登记；
- 输出可用于市场、销售、产品规划和情报分析的报告。

## 推荐阅读顺序

1. `AGENTS.md`
2. `docs/01-需求分析.md`
3. `docs/02-概要设计.md`
4. `docs/03-状态机设计.md`
5. `docs/04-接口命令.md`
6. `docs/05-WebUI设计.md`
7. `docs/06-中文数据源与CAJ处理.md`
8. `docs/07-工程风险与实施策略.md`
9. `docs/08-工作计划.md`

## 当前设计原则

- 第一版先做最小可用闭环，不追求一次性全自动。
- CLI 负责批处理、采集、解析、分析、报告导出。
- WebUI 负责人工审核、状态维护、外部链接跳转、PDF 上传、报告查看。
- Google Scholar 只作为人工跳转入口或邮件提醒线索，不做后台自动批量爬取。
- 知网、万方、维普、SinoMed、NSTL 等中文数据源先作为人工检索入口和手动导入来源。
- CAJ 文件第一版只登记，不直接解析；用户转换为 PDF 后再上传分析。

## 当前可运行能力

初始化 SQLite 数据库：

```bash
python -m src.cli init db
```

查看论文状态汇总：

```bash
python -m src.cli status summary
```

运行测试：

```bash
python -m pytest
```

默认数据库路径：

```text
data/processed/paper_analysis.sqlite
```

也可以通过环境变量覆盖：

```text
PAPER_ANALYSIS_DB=/path/to/paper_analysis.sqlite
```

## MVP 实施顺序

1. SQLite schema、repository 层、基础 CLI；
2. PubMed 摘要获取；
3. Crossref DOI 补全；
4. 去重入库与增量运行；
5. 手动 PDF 导入；
6. PDF 文本解析；
7. 证据句抽取；
8. Excel / Markdown 报告导出；
9. Streamlit WebUI 审核工作台。
