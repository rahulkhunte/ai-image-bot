# 🤖 Jenerator Bot - AI Image Generation

Telegram bot for AI image generation with a credit system, referral bonuses, three quality tiers and Telegram Stars payments. The bot forwards prompts to a separate GPU image-generation API (`GPU_API`) and sends the resulting image back to the user.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://www.python.org/)

📄 **[View Full Project Portfolio](https://rahulkhunte.github.io/portfolio/AI_Image_Bot_Portfolio.html)**

📖 **Full tutorial:** [Read on dev.to](https://dev.to/rahulkhunte/i-built-a-telegram-bot-that-generates-ai-images-using-stable-diffusion-heres-how-2n59)

> ⚠️ **Note:** Demo currently paused for infrastructure optimization. Full codebase and deployment guide available.

## ✨ Features

- 💬 **Telegram bot** - `/start` menu with inline buttons (Generate, My Credits, Buy Credits, Invite Friends)
- 💎 **Credits** - every new user gets 15 free credits
- 🎁 **Referrals** - invite link (`/start <user_id>`); the new user and the referrer each get +20 credits
- 🖼️ **Three quality tiers:**

  | Tier | Size | Cost |
  |------|------|------|
  | Standard | 512x512 | 1 credit |
  | HD | 1024x1024 | 3 credits |
  | 4K | 2048x2048 | 10 credits |

- ⭐ **Telegram Stars payments** - invoices in Stars (`XTR`) with pre-checkout and successful-payment handlers:

  | Package | Price |
  |---------|-------|
  | 100 credits | 50 Stars |
  | 500 credits | 200 Stars |
  | 1000 credits | 350 Stars |

- 🟢 **GPU health check** - `/start` pings `GPU_API/health` and shows the status
- 🎨 **Image generation** - any text message is sent as a prompt to `GPU_API/generate`; credits are deducted only when an image comes back

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Bot Framework** | python-telegram-bot 21 | Telegram API integration (long polling) |
| **Backend** | Python 3.10+ | Bot logic, credits, payments |
| **Payments** | Telegram Stars (`XTR`) | Credit purchases |
| **Image generation** | Separate GPU API (`GPU_API`) | Not included in this repo |
| **Deployment** | Docker + Railway (Procfile, nixpacks) | Containerized deployment |

## 🔌 GPU API contract

The image model runs on a separate GPU server, served by an SDXL Turbo backend (not in this repo). The bot expects:

- `GET {GPU_API}/health` → HTTP 200 when the server is up
- `POST {GPU_API}/generate` with JSON `{"prompt": "...", "size": "1024x1024"}` → image bytes (PNG)

## ⚠️ Limitations

- Credits and referrals are kept in memory and reset when the bot restarts.
- No rate limiting; generation requests are handled one at a time.
- Style prefixes such as `/anime girl` are not applied yet (messages starting with `/` don't reach the generator).

## 🚀 Deployment Guide

### Prerequisites
- Python 3.10+
- Telegram Bot Token (from @BotFather)
- A running GPU image API that implements the contract above
- Docker (optional)

### Local Setup

**1. Clone repository:**
```bash
git clone https://github.com/rahulkhunte/ai-image-bot.git
cd ai-image-bot
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Configure environment** (see `.env.example`):
```bash
BOT_TOKEN=your_token_here
GPU_API=http://your-gpu-server:8000
ADMIN_ID=0   # optional
```

**4. Launch bot:**
```bash
python bot.py
```

### Docker Deployment
```bash
docker build -t jenerator-bot .
docker run -d \
  -e BOT_TOKEN=your_token \
  -e GPU_API=http://your-gpu-server:8000 \
  jenerator-bot
```

### Railway
`Procfile` (`worker: python bot.py`) and `nixpacks.toml` are included for Railway deployment. Set `BOT_TOKEN` and `GPU_API` as environment variables.

## 🧩 Project Structure
```bash
ai-image-bot/
├── bot.py                # Bot logic: menu, credits, referrals, Stars payments, generation
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container configuration
├── Procfile              # Railway/Heroku worker
├── nixpacks.toml         # Railway build config
├── runtime.txt           # Python version
├── .env.example          # Environment variable template
└── README.md             # This file
```

## 🔮 Roadmap
- Persistent storage for credits and payments
- Rate limiting and a generation queue
- Working style prefixes and `/buy`, `/credits` commands
- Video generation
- Multiple model support

## 💼 About the Developer
Rahul Khunte - AI/ML Engineer

Available for similar projects:
- Telegram/Discord bot development
- Payment integration
- Image/video generation systems

Connect:

🌐 Portfolio: https://rahulkhunte.github.io/portfolio

💼 GitHub: https://github.com/rahulkhunte

# 📄 License
MIT License - Open for personal and commercial use

# 🙏 Acknowledgments
python-telegram-bot developers
