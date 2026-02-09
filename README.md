# LIS Scholar Skill Toolkit

面向图书馆学领域的个性化学术文献追踪工具集，基于 Claude Code Skills 框架构建。

## 概述

本项目包含四套独立的工作流，均通过 **MEMORY.md** 实现个性化的文献过滤机制：

| 工作流 | 功能 | 触发方式 | 输出 |
|--------|------|----------|------|
| **lis-journals-fetcher** | 多源期刊论文追踪 | `获取期刊论文` / `/lis-journals-fetcher` | JSON + Markdown 总结 |
| **scholar-daily-skill** | Google Scholar 日报生成 | `生成scholar日报` / `/scholar-daily` | 每日 Markdown 日报 |
| **cnki-search-agent-browser** | CNKI 检索交互工具 | `检索 CNKI 论文` / 知网相关指令 | 论文 JSON 数据 |
| **rss-daily** | RSS 智能订阅追踪 | 定时任务 / API 触发 | 向量索引 + 语义搜索 |

---

## 核心机制：MEMORY.md 个性化过滤

所有工作流共享 `MEMORY.md` 作为个性化配置中心，实现智能论文过滤。

### MEMORY.md 结构

```markdown
# 研究兴趣关键词

## 学科领域
- 图书馆学
- 信息资源组织

## 关注主题词
- 知识组织、信息组织
- 元数据、资源描述
- 大模型、RAG、知识图谱
- 智慧图书馆、AI 应用

## 排除关键词
- 元宇宙
- 公共图书馆服务
- 阅读推广活动
```

### 过滤流程

```mermaid
flowchart LR
    A[原始论文数据] --> B{读取 MEMORY.md}
    B --> C[提取研究兴趣]
    C --> D{两阶段过滤}
    D --> E[阶段1: 排除过滤]
    E --> F[包含排除关键词?]
    F -->|是| G[标记为不相关]
    F -->|否| H[阶段2: 正向匹配]
    H --> I[匹配关注主题词]
    I --> J[相关度评分]
    J --> K[输出过滤结果]
    G --> K
```

---

## 工作流详解

### 1. LIS Journals Fetcher - 多源期刊论文追踪

#### 支持的期刊类型

| 类型 | 数量 | 爬虫方式 |
|------|------|----------|
| CNKI 期刊 | 15 种 | cnki-spider-agent |
| 人大报刊复印资料 | 3 种 | rdfybk-spider-agent |
| 独立网站期刊 | 1 种 | lis-spider-agent |

#### 完整流程

```mermaid
flowchart TD
    Start([用户触发]) --> Parse[解析期刊名和年期]
    Parse --> Grep[Grep 动态搜索期刊类型]
    Grep --> Type{期刊类型识别}
    Type -->|CNKI| CNKI_Spider[cnki-spider-agent]
    Type -->|人大报刊| RDFY_Spider[rdfybk-spider-agent]
    Type -->|独立网站| LIS_Spider[lis-spider-agent]

    CNKI_Spider --> Parallel[并行爬取多期]
    RDFY_Spider --> Parallel
    LIS_Spider --> Parallel

    Parallel --> OutputJSON[输出: 期刊名/年-期.json]
    OutputJSON --> PaperFilter[paper-filter subagent]

    PaperFilter --> ReadMemory1[读取 MEMORY.md]
    ReadMemory1 --> Filter[两阶段过滤]
    Filter --> UserConfirm{人工确认修改}

    UserConfirm -->|修改| RecordChange[记录修改]
    UserConfirm -->|确认| FilterScript[filter_papers.py]
    RecordChange --> FilterScript

    FilterScript --> FilteredJSON[输出: 年-期-filtered.json]
    FilteredJSON --> Summarizer[paper-summarizer subagent]
    Summarizer --> SummaryMD[输出: 年-期-summary.md]

    UserConfirm -->|有修正| MemoryUpdate[memory-updater-agent]
    MemoryUpdate --> UpdateMEMORY[更新 MEMORY.md]
    UpdateMEMORY --> End([完成])

    style Start fill:#e1f5e1
    style End fill:#ffe1e1
    style PaperFilter fill:#ffcccc
    style ReadMemory1 fill:#ccffff
    style MemoryUpdate fill:#ccffff
```

#### 数据文件流向

```
触发
  ↓
爬取 → outputs/{期刊名}/{年-期}.json (原始数据)
  ↓
过滤 → 同一文件添加 interest_match / relevance_score 字段
  ↓
筛选 → outputs/{期刊名}/{年-期}-filtered.json (仅相关论文)
  ↓
总结 → outputs/{期刊名}/{年-期}-summary.md (Markdown 报告)
```

---

### 2. Scholar Daily Skill - Google Scholar 日报生成

#### 完整流程

```mermaid
flowchart TD
    Start([用户触发]) --> Date[解析日期参数]
    Date --> GmailSearch[gmail-skill search<br/>from:scholaralerts]

    GmailSearch --> EmailIDs[获取邮件 ID 列表]
    EmailIDs --> ParallelRead[并行读取邮件]

    ParallelRead --> SaveJSON[保存: outputs/temps/email_id.json]
    SaveJSON --> Parse[并行调用 email_formatter.py]
    Parse --> PapersJSON[保存: outputs/temps/papers_id.json]

    PapersJSON --> ParallelFilter[并行调用 scholar-email-processor]

    ParallelFilter --> ReadMemory2[每个 subagent 读取 MEMORY.md]
    ReadMemory2 --> SemanticFilter[语义过滤]

    SemanticFilter --> Discipline{学科限定}
    Discipline -->|非图书馆学| Exclude[排除]
    Discipline -->|图书馆学| ExcludeCheck{排除关键词}

    ExcludeCheck -->|触发| Exclude
    ExcludeCheck -->|未触发| TopicCheck{主题匹配}

    TopicCheck -->|不相关| Exclude
    TopicCheck -->|相关| Rate[相关度评分 ★☆☆☆☆-★★★★★]

    Rate --> Collect[汇总所有 subagent 结果]
    Collect --> Sort[按相关度排序]
    Sort --> GenerateMD[生成 Markdown 日报]

    GenerateMD --> Report[保存: outputs/scholar-reports/date-scholar-daily.md]
    Report --> DeleteEmail[删除已处理邮件]
    DeleteEmail --> Cleanup[清理 temps 目录]
    Cleanup --> End([完成])

    style Start fill:#e1f5e1
    style End fill:#ffe1e1
    style ParallelFilter fill:#ffcccc
    style ReadMemory2 fill:#ccffff
    style SemanticFilter fill:#ffffcc
```

#### scholar-email-processor 过滤逻辑

| 优先级 | 过滤规则 | 说明 |
|--------|----------|------|
| 1 | 学科领域限定 | 必须属于图书馆学/信息资源组织领域 |
| 2 | 排除规则 | 元宇宙、公共图书馆服务等直接排除 |
| 3 | 主题匹配 | 与关注主题词（知识组织、大模型等）相关 |
| 4 | 相关度评分 | ★★★★★ 到 ★☆☆☆☆ |

---

### 3. CNKI Search Agent - CNKI 检索交互工具

#### 交互式流程

```mermaid
flowchart TD
    Start([用户触发]) --> Detect{检测用户表达}
    Detect -->|含关键词| ParamStep[询问检索参数]
    Detect -->|仅触发意图| TypeStep[选择检索类型]

    TypeStep --> AskUser[AskUserQuestion]
    AskUser --> Simple{简单检索?}
    Simple -->|是| ParamStep
    Simple -->|否| ParamStep

    ParamStep --> Confirm[展示检索条件确认]
    Confirm --> Execute[调用脚本执行]

    Execute --> Script{选择脚本}
    Script -->|简单检索| SearchScript[cnki-search.sh]
    Script -->|高级检索| AdvSearchScript[cnki-adv-search.sh]

    SearchScript --> AgentBrowser[agent-browser 自动化]
    AdvSearchScript --> AgentBrowser

    AgentBrowser --> Result[展示爬取结果]
    Result --> HasRemaining{有剩余文献?}
    HasRemaining -->|是| Continue{继续爬取?}
    HasRemaining -->|否| EndStep[关闭会话结束]

    Continue -->|是| CrawlStep[cnki-crawl.sh 延续爬取]
    CrawlStep --> Result
    Continue -->|否| EndStep
    EndStep --> End([完成])

    style Start fill:#e1f5e1
    style End fill:#ffe1e1
    style AgentBrowser fill:#ffffcc
    style TypeStep fill:#ccffcc
```

#### agent-browser 约束

| 约束 | 说明 |
|------|------|
| **有头模式** | `--headed` 参数（无头模式会被检测） |
| **Session 管理** | `--session` 参数启动会话 |
| **元素 ref** | 动态变化，需使用 `snapshot -i` 获取最新 ref |

---

### 4. RSS Daily Skill - RSS 智能订阅追踪

> https://github.com/xulei-shl/lis-rss-daily

#### 核心特点

| 特性 | 说明 |
|------|------|
| **自动抓取** | node-cron 定时抓取 RSS 源，支持并发控制 |
| **LLM 智能过滤** | 基于研究兴趣自动判断文章相关性 |
| **向量索引** | ChromaDB 语义向量存储 |
| **增量刷新** | 新文章自动触发老文章相关列表更新 |

#### 完整流程

```mermaid
flowchart TD
    Start([定时触发]) --> Schedule[RSS Scheduler]
    Schedule --> Parse[RSS Parser 解析]
    Parse --> Dedup{去重检查}

    Dedup -->|已存在| Skip[跳过]
    Dedup -->|新文章| SaveDB[保存到数据库]

    SaveDB --> Filter[LLM Filter 智能过滤]
    Filter --> ReadMemory4[依据 MEMORY.md]
    ReadMemory4 --> Judge{相关性判断}

    Judge -->|拒绝| MarkRejected[标记为 rejected]
    Judge -->|通过| Pipeline[处理流水线]

    Pipeline --> Clean[Markdown 清洗]
    Clean --> Translate[LLM 翻译 EN→CN]
    Translate --> Vector[向量索引 ChromaDB]
    Vector --> Related[计算相关文章]

    Related --> Incremental{增量刷新}
    Incremental --> RefreshOld[刷新老文章相关列表]
    RefreshOld --> CacheDB[更新 article_related 表]

    CacheDB --> Search[语义搜索可用]
    MarkRejected --> End([完成])
    Search --> End

    style Start fill:#e1f5e1
    style End fill:#ffe1e1
    style Filter fill:#ffcccc
    style ReadMemory4 fill:#ccffff
    style Pipeline fill:#ffffcc
    style CacheDB fill:#ccffcc
```

#### 个人 Memory 共享机制

**相关文章缓存系统** (`article_related` 表)：

1. **增量刷新**：新文章处理完成后，自动找到相似老文章并刷新其相关列表
2. **周期性刷新**：定时刷新过期缓存（默认7天），优先刷新近期文章
3. **语义关联**：基于向量相似度构建"活的知识图谱"

---

## 共享架构图

```mermaid
graph TB
    subgraph Workflows["四大工作流"]
        W1[LIS Journals Fetcher]
        W2[Scholar Daily Skill]
        W3[CNKI Search Agent]
        W4[RSS Daily Skill]
    end

    subgraph Filters["过滤 Subagents"]
        F1[paper-filter]
        F2[scholar-email-processor]
        F4[LLM Filter]
    end

    subgraph Spiders["爬虫 Subagents"]
        S1[cnki-spider-agent]
        S2[rdfybk-spider-agent]
        S3[lis-spider-agent]
    end

    subgraph Outputs["输出处理"]
        O1[paper-summarizer]
        O2[memory-updater-agent]
    end

    subgraph Core["共享核心"]
        M[(MEMORY.md<br/>个性化配置)]
        V[(向量索引<br/>语义关联)]
    end

    W1 --> S1 & S2 & S3
    W1 --> F1
    W2 --> F2
    W4 --> F4

    F1 --> M
    F2 --> M
    F4 --> M

    F1 --> O1
    O1 -.->|条件触发| O2
    O2 --> M

    W3 --> B[agent-browser]
    W4 --> V

    classDef workflow fill:#e1f5e1,stroke:#333,stroke-width:2px
    classDef filter fill:#ffcccc,stroke:#333,stroke-width:2px
    classDef spider fill:#ffffcc,stroke:#333,stroke-width:2px
    classDef output fill:#ccffcc,stroke:#333,stroke-width:2px
    classDef memory fill:#ccffff,stroke:#333,stroke-width:2px

    class W1,W2,W3,W4 workflow
    class F1,F2,F4 filter
    class S1,S2,S3 spider
    class O1,O2 output
    class M,V memory
```

---

## Subagent 列表

### 爬虫类 Subagents

| Subagent | 文件 | 作用 |
|----------|------|------|
| cnki-spider-agent | `.claude/agents/cnki-spider-agent.md` | CNKI 期刊爬取 |
| rdfybk-spider-agent | `.claude/agents/rdfybk-spider-agent.md` | 人大报刊复印资料爬取 |
| lis-spider-agent | `.claude/agents/lis-spider-agent.md` | 独立网站期刊爬取 |

### 过滤类 Subagents

| Subagent | 文件 | 作用 |
|----------|------|------|
| paper-filter | `.claude/agents/paper-filter.md` | 期刊论文智能过滤标注 |
| scholar-email-processor | `.claude/agents/scholar-email-processor.md` | Scholar 邮件论文过滤 |

### 总结类 Subagents

| Subagent | 文件 | 作用 |
|----------|------|------|
| paper-summarizer | `.claude/agents/paper-summarizer.md` | 生成论文总结报告 |

### 记忆更新类 Subagents

| Subagent | 文件 | 作用 |
|----------|------|------|
| memory-updater-agent | `.claude/agents/memory-updater-agent.md` | 智能更新 MEMORY.md |

---

### RSS Daily 模块

| 模块 | 文件 | 作用 |
|------|------|------|
| RSS Scheduler | `src/rss-scheduler.ts` | 定时抓取 RSS 源 |
| LLM Filter | `src/filter.ts` | 基于研究兴趣智能过滤 |
| Pipeline | `src/pipeline.ts` | 翻译、向量化、相关文章计算 |
| Vector Indexer | `src/vector/indexer.ts` | ChromaDB 向量索引服务 |
| Related Refresh | `src/related-scheduler.ts` | 增量刷新相关文章缓存 |

---

## 目录结构

```
lis-scholar-skill-toolkit/
├── .claude/
│   ├── skills/                    # Skill 工作流
│   │   ├── lis-journals-fetcher/  # 期刊论文获取
│   │   ├── scholar-daily-skill/   # Scholar 日报生成
│   │   ├── cnki-search-agent-browser/  # CNKI 检索
│   │   ├── gmail-skill/           # Gmail 访问
│   │   ├── agent-browser/         # 浏览器自动化
│   │   ├── json-canvas/           # Canvas 绘图
│   │   └── memory-updater/        # 记忆更新
│   └── agents/                    # Subagent 定义
│       ├── cnki-spider-agent.md
│       ├── rdfybk-spider-agent.md
│       ├── lis-spider-agent.md
│       ├── paper-filter.md
│       ├── scholar-email-processor.md
│       ├── paper-summarizer.md
│       └── memory-updater-agent.md
├── src/                           # RSS Daily 核心代码
│   ├── rss-scheduler.ts           # RSS 定时抓取
│   ├── filter.ts                  # LLM 智能过滤
│   ├── pipeline.ts                # 文章处理流水线
│   └── vector/                    # 向量索引服务
├── outputs/                       # 输出目录
│   ├── {期刊名}/                  # 期刊论文数据
│   ├── scholar-reports/           # Scholar 日报
│   └── temps/                     # 临时文件
├── MEMORY.md                      # 个性化配置（需用户创建）
└── README.md
```

---

## 快速开始

### 1. 创建 MEMORY.md

在项目根目录创建 `MEMORY.md` 文件，定义你的研究兴趣：

```markdown
# 研究兴趣关键词

## 学科领域
- 图书馆学
- 信息资源管理

## 关注主题词
- 知识组织
- 元数据
- 大模型
- RAG

## 排除关键词
- 元宇宙
```

### 2. 使用工作流

```bash
# 获取期刊论文
/lis-journals-fetcher

# 生成 Scholar 日报
/scholar-daily

# 检索 CNKI 论文
检索 CNKI 论文

# RSS 订阅（自动运行）
npm start
```