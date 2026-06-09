STYLE_DESCRIPTIONS = {
    "analyst": {
        "zh": "机构级分析师风格：数据驱动，逻辑严密，客观专业。引用具体数据和链上指标，分析底层逻辑，结论有据可查。避免情绪化表达，用事实说话。",
        "en": "Institutional analyst style: data-driven, rigorous logic, objective and professional. Reference specific data and on-chain metrics, analyze underlying logic, conclusions are well-supported. Avoid emotional language, let facts speak.",
    },
    "kol": {
        "zh": "加密KOL叙事风格：有强烈个人观点，接地气，善用crypto圈黑话（打新、撸毛、叙事、alpha、土狗、链上数据、筹码结构等）。有情绪感染力，让读者有共鸣，敢于给出明确判断。",
        "en": "Crypto KOL narrative style: strong personal opinions, relatable, uses crypto slang freely (alpha, narrative, degen, on-chain, etc.). Emotionally engaging, creates resonance with readers, gives clear decisive takes.",
    },
    "official": {
        "zh": "项目方官方风格：正式庄重，强调里程碑与生态进展，用词积极正面。突出技术创新、合作伙伴、社区成就。语气自信，代表团队发声。",
        "en": "Official project style: formal and authoritative, highlights milestones and ecosystem progress, positive framing. Emphasizes technical innovation, partnerships, community achievements. Confident tone, speaking on behalf of the team.",
    },
}

WECHAT_FORMAT = {
    "zh": """格式要求：
- 总字数 800-1500 字
- 结构：开篇钩子（引发好奇/共鸣）→ 核心事件/数据（What happened）→ 深度解读（Why it matters）→ 对读者的意义（So what）→ 结尾行动号召
- 用小标题分段（加粗或 ## 格式）
- 数据和关键词可以**加粗**
- 结尾留一个引发互动的问题或观点""",
    "en": """Format requirements:
- 600-1200 words
- Structure: Hook (curiosity/resonance) → Core event/data (What happened) → Deep analysis (Why it matters) → Reader implications (So what) → CTA closing
- Use subheadings (bold or ## format)
- Bold key data and keywords
- End with an engaging question or strong take""",
}

TWITTER_FORMAT = {
    "zh": """格式要求：
- 5-8 条推文组成的 Thread
- 每条 ≤280 字符（中文约140字）
- 第1条：强力钩子，让人必须点"显示更多"
- 中间：每条聚焦一个核心观点，可带数据
- 最后一条：互动问题或总结性金句
- 每条前加序号，如 1/ 2/ 3/
- 不要加 hashtag（显得spam）""",
    "en": """Format requirements:
- 5-8 tweet thread
- Each tweet ≤280 characters
- Tweet 1: strong hook, must make readers click "show more"
- Middle tweets: one key point each, with data when available
- Last tweet: engagement question or memorable conclusion
- Number each tweet: 1/ 2/ 3/
- No hashtags (looks spammy)""",
}


def build_system_prompt(language: str) -> str:
    if language == "zh":
        return """你是一个深度理解加密货币行业的内容创作专家，同时也是一个资深的中文 crypto 媒体人。

你对以下领域有深刻理解：
- DeFi、L1/L2、NFT、GameFi、RWA、AI+Crypto 等各类叙事
- 链上数据解读（TVL、DEX 交易量、鲸鱼动向、资金费率、持仓结构）
- Crypto 市场周期、资本流向、做市商行为
- 中文 crypto 社区的语言习惯和内容偏好

你写出的内容应该：
- 像一个真正的 crypto insider 写的，不像 AI 生成
- 有具体的数据支撑，不说空话
- 理解读者的认知背景（他们懂基础概念，不需要解释什么是区块链）
- 有明确的信息增量，读完有收获"""
    else:
        return """You are a deep crypto content expert and seasoned crypto media writer.

You have deep knowledge of:
- DeFi, L1/L2, NFT, GameFi, RWA, AI+Crypto narratives
- On-chain data interpretation (TVL, DEX volume, whale movements, funding rates, position structure)
- Crypto market cycles, capital flows, market maker behavior
- English crypto community language and content conventions

Your content should:
- Read like a real crypto insider wrote it, not AI-generated
- Be backed by specific data, no empty claims
- Assume reader knowledge (they understand basic concepts)
- Deliver clear information value — readers learn something"""


def build_prompt(
    raw_material: str,
    content_types: list[str],
    style: str,
    language: str,
) -> tuple[str, str]:
    style_desc = STYLE_DESCRIPTIONS.get(style, STYLE_DESCRIPTIONS["kol"])[language]

    sections = []

    if "wechat" in content_types:
        label = "【公众号长文】" if language == "zh" else "【WeChat Article】"
        sections.append(f"{label}\n{WECHAT_FORMAT[language]}")

    if "twitter" in content_types:
        label = "【X Thread】"
        sections.append(f"{label}\n{TWITTER_FORMAT[language]}")

    sep = "---" * 10

    if language == "zh":
        user_prompt = f"""请根据以下原始素材，按照指定风格和格式生成内容。

**写作风格：** {style_desc}

**原始素材：**
{raw_material}

**输出要求：**
{chr(10).join(sections)}

{sep}
请直接输出内容，不要加前言或解释。如需同时输出多种格式，用清晰的标题分隔。"""
    else:
        user_prompt = f"""Generate content based on the following raw material, using the specified style and format.

**Writing style:** {style_desc}

**Raw material:**
{raw_material}

**Output requirements:**
{chr(10).join(sections)}

{sep}
Output the content directly, no preamble or explanation. If generating multiple formats, separate them with clear headers."""

    return build_system_prompt(language), user_prompt
