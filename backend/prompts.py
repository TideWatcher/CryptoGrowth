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
    "humorous": {
        "zh": "幽默风趣风格：语言生动有梗，善用比喻、自嘲和适度调侃，把专业内容讲得轻松易懂，但不流于浮夸，关键信息依然准确到位。",
        "en": "Humorous style: lively and witty, uses analogies, memes and light self-deprecating humor to make technical content easy and fun to read, without sacrificing accuracy on key facts.",
    },
    "rigorous": {
        "zh": "科学严谨风格：用词精确克制，逻辑链条清晰，强调数据来源和方法论，区分事实与推测，避免夸大或绝对化的表述。",
        "en": "Scientific/rigorous style: precise and measured language, clear logical chain, emphasizes data sources and methodology, clearly separates facts from speculation, avoids exaggeration or absolute claims.",
    },
    "storytelling": {
        "zh": "故事化叙事风格：用场景、人物和情节展开内容，把抽象的加密概念和数据转化为有画面感的故事，增强代入感和记忆点，结尾呼应开头。",
        "en": "Storytelling style: builds the content around a scene, characters or a narrative arc, turning abstract crypto concepts and data into a vivid story that's memorable and easy to relate to, with a closing that echoes the opening.",
    },
}

LANGUAGE_NAMES = {
    "zh": "Chinese (中文)",
    "en": "English",
    "ja": "Japanese (日本語)",
    "ko": "Korean (한국어)",
    "ru": "Russian (Русский)",
    "pt": "Portuguese (Português)",
}

WECHAT_LENGTH_SPECS = {
    "600-1000": {"zh": "600-1000 字", "en": "600-1000 words"},
    "1000-1500": {"zh": "1000-1500 字", "en": "1000-1500 words"},
    "1500+": {"zh": "1500 字以上（可视内容丰富程度写到 2000-2500 字）", "en": "over 1500 words (up to 2000-2500 words if the material supports it)"},
}

TWITTER_LENGTH_SPECS = {
    "single": {
        "zh": """- 输出为单条 X 长文 Post，不使用 1/ 2/ 3/ 编号，不拆分成多条
- 用换行分段，总长度约 400-800 字
- 第一句话是钩子，必须抓住注意力
- 结尾给出明确观点或互动引导""",
        "en": """- Output as a single long-form X post, no 1/ 2/ 3/ numbering, no thread
- Use line breaks for paragraphs, total length ~300-600 words
- First line is the hook and must grab attention
- End with a clear take or a call to engage""",
    },
}


def _twitter_thread_spec(language: str, n: int) -> str:
    if language == "zh":
        return f"""- 由 {n} 条推文组成的 Thread
- 每条 ≤280 字符（中文约140字）
- 第1条：强力钩子，让人必须点"显示更多"
- 中间：每条聚焦一个核心观点，可带数据
- 最后一条：互动问题或总结性金句
- 每条前加序号，如 1/ 2/ 3/，共 {n} 条
- 不要加 hashtag（显得spam）"""
    return f"""- A {n}-tweet thread
- Each tweet <=280 characters
- Tweet 1: strong hook, must make readers click "show more"
- Middle tweets: one key point each, with data when available
- Last tweet: engagement question or memorable conclusion
- Number each tweet: 1/ 2/ 3/, exactly {n} tweets total
- No hashtags (looks spammy)"""


def _twitter_format(language: str, twitter_length: str) -> str:
    if twitter_length == "single":
        return TWITTER_LENGTH_SPECS["single"][language]
    try:
        n = int(twitter_length)
    except (TypeError, ValueError):
        n = 5
    return _twitter_thread_spec(language, n)


def _wechat_format(language: str, wechat_length: str) -> str:
    length_text = WECHAT_LENGTH_SPECS.get(wechat_length, WECHAT_LENGTH_SPECS["1000-1500"])[language]
    if language == "zh":
        return f"""格式要求：
- 总字数 {length_text}
- 结构：开篇钩子（引发好奇/共鸣）→ 核心事件/数据（What happened）→ 深度解读（Why it matters）→ 对读者的意义（So what）→ 结尾行动号召
- 用小标题分段（加粗或 ## 格式）
- 数据和关键词可以**加粗**
- 结尾留一个引发互动的问题或观点"""
    return f"""Format requirements:
- {length_text}
- Structure: Hook (curiosity/resonance) -> Core event/data (What happened) -> Deep analysis (Why it matters) -> Reader implications (So what) -> CTA closing
- Use subheadings (bold or ## format)
- Bold key data and keywords
- End with an engaging question or strong take"""


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
    return """You are a deep crypto content expert and seasoned crypto media writer.

You have deep knowledge of:
- DeFi, L1/L2, NFT, GameFi, RWA, AI+Crypto narratives
- On-chain data interpretation (TVL, DEX volume, whale movements, funding rates, position structure)
- Crypto market cycles, capital flows, market maker behavior
- Crypto community language and content conventions across languages

Your content should:
- Read like a real crypto insider wrote it, not AI-generated
- Be backed by specific data, no empty claims
- Assume reader knowledge (they understand basic concepts)
- Deliver clear information value -- readers learn something"""


def _style_description(styles: list[str], language: str) -> str:
    valid = [s for s in styles if s in STYLE_DESCRIPTIONS] or ["kol"]
    valid = valid[:3]
    descs = [STYLE_DESCRIPTIONS[s][language] for s in valid]
    if len(descs) == 1:
        return descs[0]
    if language == "zh":
        bullets = "\n".join(f"- {d}" for d in descs)
        return f"请融合以下多种风格特点：\n{bullets}"
    bullets = "\n".join(f"- {d}" for d in descs)
    return f"Blend the following style traits together:\n{bullets}"


def build_prompt(
    raw_material: str,
    content_types: list[str],
    styles: list[str],
    language: str,
    wechat_length: str = "1000-1500",
    twitter_length: str = "5",
) -> tuple[str, str]:
    prompt_lang = "zh" if language == "zh" else "en"
    style_desc = _style_description(styles, prompt_lang)

    sections = []

    if "wechat" in content_types:
        label = "【公众号长文】" if prompt_lang == "zh" else "【WeChat Article】"
        sections.append(f"{label}\n{_wechat_format(prompt_lang, wechat_length)}")

    if "twitter" in content_types:
        label = "【X Thread】"
        sections.append(f"{label}\n{_twitter_format(prompt_lang, twitter_length)}")

    sep = "---" * 10

    output_language_name = LANGUAGE_NAMES.get(language, "English")

    if prompt_lang == "zh":
        language_line = "请用中文输出全部内容。" if language == "zh" else f"请用 {output_language_name} 输出全部内容（说明文字也用该语言）。"
        user_prompt = f"""请根据以下原始素材，按照指定风格和格式生成内容。

**写作风格：** {style_desc}

**原始素材：**
{raw_material}

**输出要求：**
{chr(10).join(sections)}

**输出语言：** {language_line}

{sep}
请直接输出内容，不要加前言或解释。如需同时输出多种格式，用清晰的标题分隔。"""
    else:
        language_line = f"Write all output content in {output_language_name}."
        user_prompt = f"""Generate content based on the following raw material, using the specified style and format.

**Writing style:** {style_desc}

**Raw material:**
{raw_material}

**Output requirements:**
{chr(10).join(sections)}

**Output language:** {language_line}

{sep}
Output the content directly, no preamble or explanation. If generating multiple formats, separate them with clear headers."""

    return build_system_prompt(prompt_lang), user_prompt
