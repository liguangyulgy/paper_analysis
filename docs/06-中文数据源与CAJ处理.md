# 06-中文数据源与CAJ处理

## 1. 是否需要中文数据源

如果研究 genOway / 基锘威在中国境内的应用情况，英文源不够。英文源适合确认高质量论文证据，中文源适合发现中国境内机构、课题组、硕博论文、会议论文和市场线索。

建议定位：

```text
英文源：正式论文主线和高质量证据
中文源：国内应用线索和补充证据
```

## 2. 中文数据源分层

### 2.1 第一优先级

- CNKI / 中国知网；
- 万方；
- SinoMed 中国生物医学文献服务系统。

适用场景：

- 中文期刊；
- 硕博论文；
- 医学、生物医学、药学相关论文；
- 国内高校、医院、科研院所应用线索。

### 2.2 第二优先级

- 维普；
- NSTL 国家科技图书文献中心。

适用场景：

- 中文期刊补充；
- 会议、科技报告、标准、专利等线索补充。

### 2.3 第三优先级

后续可扩展：

- 国家知识产权局专利检索；
- 企业官网新闻；
- 药企管线新闻；
- 展会资料；
- 公众号文章；
- 招投标和采购信息。

这些更偏市场情报，不建议第一版纳入论文系统主链路。

## 3. 工程边界

第一版不自动爬取中文数据库。

原因：

- 中文数据库通常没有稳定开放 API；
- 全文下载常受订阅限制；
- 自动抓取存在反爬和合规风险；
- 格式可能是 PDF、CAJ、HTML；
- 元数据质量和重复情况更复杂。

第一版只支持：

- WebUI 跳转中文数据库检索；
- 手动录入中文论文元数据；
- 导入中文数据库导出的题录文件；
- 上传中文 PDF；
- 上传 CAJ 并登记为待转换。

## 4. 中文关键词配置

新增：

```text
configs/chinese_queries.yaml
```

示例：

```yaml
company_keywords:
  - "基锘威"
  - "genOway"
  - "基锘威 生物"
  - "基锘威 动物模型"

model_keywords:
  - "人源化小鼠"
  - "人源化动物模型"
  - "免疫系统人源化"
  - "免疫缺陷小鼠"
  - "肿瘤免疫模型"
  - "基因敲入小鼠"
  - "基因敲除小鼠"
  - "FcRn 人源化"
  - "IgE 人源化"
  - "BRGSF"

application_keywords:
  - "药效评价"
  - "安全性评价"
  - "药代动力学"
  - "PK/PD"
  - "靶点验证"
  - "肿瘤免疫"
  - "过敏反应"
  - "炎症模型"
  - "阿尔茨海默病"
```

## 5. 中文检索入口

WebUI 提供按钮：

- 打开 CNKI 检索；
- 打开万方检索；
- 打开维普检索；
- 打开 SinoMed 检索；
- 打开 NSTL 检索；
- 手动录入中文论文；
- 上传中文 PDF / CAJ；
- 导入题录文件。

## 6. 中文论文状态

建议新增字段：

```text
language = zh / en / mixed / unknown
region_relevance = china_domestic / global / unknown / not_china_related
source_type = english_literature / chinese_literature_lead / manual_upload
```

中文数据库来的结果默认：

```text
review_status = needs_review
reference_value = unknown
source_type = chinese_literature_lead
region_relevance = china_domestic 或 unknown
```

人工确认后可标记为：

- 中国境内应用证据；
- 中国境内应用线索；
- 国内机构相关；
- 国内市场参考价值高。

## 7. CAJ 文件处理策略

第一版不直接解析 CAJ。

原因：

- CAJ 解析生态不如 PDF 稳定；
- 自动转换通常依赖桌面软件；
- 文件权限和版权边界复杂；
- 企业内使用不宜依赖不可信在线转换网站。

第一版处理流程：

```text
用户上传 CAJ
        ↓
系统识别 file_type = caj
        ↓
登记文件和论文信息
        ↓
设置 fulltext_status = conversion_needed
        ↓
设置 parse_status = conversion_needed
        ↓
提示用户转换为 PDF 后重新上传
```

用户提示文案：

```text
该文件为 CAJ 格式，系统暂不直接解析。
请使用 CAJViewer 等本地工具打开，并导出或打印为 PDF 后重新上传。
不要将敏感或受版权限制的 CAJ 上传到不可信在线转换网站。
```

## 8. 中文报告

报告中应单独增加：

- 中国境内应用线索；
- 中文论文清单；
- 中文高价值候选；
- 国内机构 / 作者单位分析；
- 中文全文缺失；
- CAJ 待转换清单。

## 9. 分阶段建议

第一阶段：

```text
支持中文论文手动录入 + 中文 PDF 上传解析
```

第二阶段：

```text
WebUI 增加 CNKI / 万方 / 维普 / SinoMed / NSTL 检索入口
```

第三阶段：

```text
支持中文数据库导出的题录文件导入
```

第四阶段：

```text
中文论文分析报告单独成章：中国境内应用线索
```
