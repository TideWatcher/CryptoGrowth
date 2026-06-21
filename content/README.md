# content/ — 日常内容生产与归档

TideWatcher（cao）的内容仓库。每天产出的 X 推文、公众号长文、知乎回答、触达话术等
都按「日期 + 平台」归档在这里，方便复用、二次加工，以及把 X 钩子帖直接喂给
CryptoWrite 二次扩写。

线上工具：CryptoWrite — https://write.tidewatcher.xyz
联系方式：Telegram — t.me/TideWatcher_cao

---

## 目录结构

```
content/
  README.md            # 本文件：归档约定与工作流
  templates/           # 各平台可复用模板（照着填）
    x-tweet.md           # X 单条推文（观点 / 数据案例）
    x-thread.md          # X 长线程 Thread
    wechat-article.md    # 微信公众号长文
    zhihu-answer.md      # 知乎回答
    growth-diagnosis.md  # 增长诊断一页纸（销售动作）
    wechat-outreach.md   # 微信一对一触达话术
  YYYY-MM-DD/          # 按日期归档，每天一个文件夹
    x.md                 # 当天 X 内容（推文 + Thread）
    wechat.md            # 当天/当周公众号内容
    zhihu.md             # 当天知乎回答
    notes.md             # 当天的素材碎片、灵感、未成稿
  ideas.md             # 选题与灵感的长期蓄水池（随手记）
```

> 不必每个平台每天都建文件——当天产了什么就建什么。空文件夹不留。

---

## 命名约定

- 日期文件夹用 `YYYY-MM-DD`（如 `2026-06-19`），保证按时间排序。
- 平台文件用小写平台名：`x.md` / `wechat.md` / `zhihu.md` / `linkedin.md`。
- 一天内同平台多篇，用 `x-1.md` / `x-2.md`，或在同一文件内用 `---` 分隔。

---

## 每篇内容的 frontmatter（便于检索与复用）

每个成稿文件顶部建议带一段元信息：

```
---
date: 2026-06-19
platform: x            # x / wechat / zhihu / linkedin
type: thread           # tweet / thread / article / answer / outreach / diagnosis
status: draft          # draft / ready / published
topic: 冷启动增长
cryptowrite: true      # 是否计划喂给 CryptoWrite 二次扩写
source: ""             # 原始素材链接或出处
---
```

`status: ready` 表示可直接发布；`published` 后可在末尾补一行发布链接与数据回收
（点赞/转发/涨粉/带来的咨询），用于复盘哪类内容转化最高。

---

## 工作流

1. **攒素材** → 随手丢进当天 `notes.md` 或 `ideas.md`。
2. **成稿** → 套 `templates/` 里的模板，写进当天对应平台文件，`status: draft`。
3. **定稿** → 改到 `status: ready`，复制发布。
4. **复盘** → 发布后回填链接和数据，沉淀「什么内容带来咨询」的规律。
5. **二次加工** → 标了 `cryptowrite: true` 的 X 钩子帖，可整段喂给 CryptoWrite
   扩写成公众号长文或多语言 Thread，一稿多投。

---

## 内容原则（贴在最显眼处）

> **内容 ≠ 广告，内容 = 你解决问题的证明。**
> 每一条发出去的东西，要让人觉得"这个人懂，我有问题想找他聊"，
> 而不是"这个人在卖东西"。
