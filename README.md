# CryptoWrite (CryptoGrowth)

AI 驱动的加密货币内容创作工具。粘贴一段原始素材（新闻、推文、研报片段等），一键生成适合**微信公众号长文**和 **X (Twitter) Thread** 的内容，支持多种写作风格、多种语言和多种长度规格。

线上地址：https://write.tidewatcher.xyz

---

## 功能特性

### 内容生成
- **输入**：粘贴任意原始素材（中文/英文均可）
- **输出格式**（可多选）：
  - 微信公众号长文，长度可选 600-1000 / 1000-1500 / 1500+ 字
  - X Thread，可选整段文案，或 3 / 4 / 5 / 6 / 7 条的 Thread
- **写作风格**（最多同时叠加 3 种）：
  - KOL 叙事 / 分析师 / 项目方官方 / 幽默风趣 / 科学严谨 / 故事化叙事
- **输出语言**：中文 / English / 日本語 / 한국어 / Русский / Português
- 一键复制全文，X Thread 可单独复制"第 1 条"用于发布

### 用户系统
- 邮箱注册/登录，密码使用 bcrypt 哈希
- 支持 Google OAuth 登录
- 基于 Cookie 的 JWT 鉴权
- 新用户赠送 5 次免费生成额度

### 订阅与支付
$8.88 / 月，解锁无限生成。支持三种支付方式：

| 方式 | 说明 |
| --- | --- |
| **USDT (TRC20)**（推荐） | 用户转账后提交交易哈希，人工审核（`admin_review.py` 自动从 TronScan 拉取交易详情辅助核对），通过后开通 30 天订阅 |
| **银行卡 / VISA（Stripe）** | Stripe Checkout 订阅模式，自动续费，webhook 同步订阅状态 |
| **国际卡 / VISA（Airwallex）** | Airwallex 托管支付链接，作为 Stripe 的备用方案，webhook 同步订阅状态 |

各支付渠道是否显示由 `/payments/config` 接口根据后端是否配置了对应密钥自动控制。

---

## 技术架构

- **后端**：FastAPI + SQLAlchemy + SQLite
- **前端**：原生 HTML / CSS / JavaScript（无构建步骤）
- **AI**：Anthropic Claude API（`claude-sonnet-4-6`）
- **部署**：单个 Docker 容器，Caddy 反向代理

```
backend/
  main.py        # FastAPI 路由：鉴权、生成、支付
  auth.py        # 密码哈希、JWT、Google OAuth
  database.py    # SQLAlchemy 模型（User / USDTPayment）
  payments.py    # Stripe 订阅相关
  airwallex.py   # Airwallex 支付链接 + webhook 签名校验
  prompts.py     # AI 提示词构建（风格/语言/长度）
  admin_review.py # USDT 转账人工审核 CLI 工具
frontend/
  index.html
  app.js         # 生成页面逻辑
  auth.js        # 登录/注册弹窗
  payment.js     # 付费弹窗与支付渠道
  style.css
```

---

## 本地开发

```bash
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env   # 填入各项密钥
uvicorn main:app --reload
```

访问 `http://localhost:8000` 即可。

## 部署

```bash
docker compose up -d --build
```

容器会读取项目根目录的 `.env` 文件（参见 `.env.example`）。数据库文件持久化在 `./data/app.db`。

---

## 环境变量

| 变量 | 必填 | 说明 |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | ✅ | Claude API Key |
| `JWT_SECRET` | ✅ | 用于签发登录 token，建议随机 32 位字符串 |
| `USDT_ADDRESS_TRC20` | ✅ | 用于接收 USDT 转账的 TRC20 地址 |
| `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` | 可选 | 启用 Stripe 银行卡支付 |
| `AIRWALLEX_CLIENT_ID` / `AIRWALLEX_API_KEY` / `AIRWALLEX_WEBHOOK_SECRET` / `AIRWALLEX_ENV` | 可选 | 启用 Airwallex 国际卡支付（`AIRWALLEX_ENV` 取值 `demo` 或 `prod`） |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI` | 可选 | 启用 Google 登录 |

完整列表见 `.env.example`。

---

## 运营：USDT 支付审核

用户提交 USDT 转账的交易哈希后，状态为 `pending`。在容器内运行：

```bash
docker exec -it cryptowrite-app-1 python3 admin_review.py
```

工具会逐条拉取 TronScan 上的交易详情（金额、收款地址、链上确认状态），并提示与配置的 `USDT_ADDRESS_TRC20` 和订阅价格做核对，审核员可选择批准（开通 30 天订阅）或拒绝（记录拒绝原因）。
