import os
import io
import sys
import logging
import requests
from telegram import LabeledPrice, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    PreCheckoutQueryHandler, filters, ContextTypes
)

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Config — loaded strictly from environment
# Never hardcode secrets or IPs here
# ──────────────────────────────────────────────
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GPU_API   = os.environ.get('GPU_API')          # e.g. http://your-server:8000
ADMIN_ID  = int(os.environ.get('ADMIN_ID', 0)) # optional, safe default

FREE_CREDITS   = 15
REFERRAL_BONUS = 20

# ──────────────────────────────────────────────
# Validate required env vars at startup
# ──────────────────────────────────────────────
def _validate_env() -> bool:
    missing = []
    if not BOT_TOKEN:
        missing.append('BOT_TOKEN')
    if not GPU_API:
        missing.append('GPU_API')
    if missing:
        logger.critical(
            "Missing required environment variables: %s\n"
            "Set them before starting the bot. See .env.example.",
            ', '.join(missing)
        )
        return False
    return True

# ──────────────────────────────────────────────
# In-memory storage (replace with DB for prod)
# ──────────────────────────────────────────────
user_credits   = {}
user_referrals = {}

# ──────────────────────────────────────────────
# Styles & Quality Tiers
# ──────────────────────────────────────────────
STYLES = {
    'pfp':       'pfp style, profile picture, avatar, clean background',
    'anime':     'anime style, vibrant colors, detailed',
    'cyberpunk': 'cyberpunk style, neon, futuristic',
    'pixel':     'pixel art style, 8bit, retro',
    'abstract':  'abstract art, colorful, unique',
    '3d':        '3d rendered, high quality, detailed',
    'fantasy':   'fantasy art, magical, ethereal',
}

QUALITY_TIERS = {
    'standard': {'size': '512x512',   'credits': 1,  'name': 'Standard'},
    'hd':       {'size': '1024x1024', 'credits': 3,  'name': 'HD'},
    '4k':       {'size': '2048x2048', 'credits': 10, 'name': '4K'},
}

# ──────────────────────────────────────────────
# Handlers
# ──────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # Handle referral
    if context.args:
        try:
            referrer_id = int(context.args[0])
            if referrer_id != user_id and user_id not in user_credits:
                user_credits[user_id] = FREE_CREDITS + REFERRAL_BONUS
                user_credits[referrer_id] = user_credits.get(referrer_id, 0) + REFERRAL_BONUS
                user_referrals[referrer_id] = user_referrals.get(referrer_id, 0) + 1

                await update.message.reply_text(
                    f"🎉 Welcome! You got {FREE_CREDITS + REFERRAL_BONUS} credits!\n"
                    f"(+{REFERRAL_BONUS} bonus from referral!)"
                )
                try:
                    await context.bot.send_message(
                        referrer_id,
                        f"🎁 Friend joined! You got +{REFERRAL_BONUS} credits!"
                    )
                except Exception:
                    pass
        except (ValueError, IndexError):
            logger.warning("Invalid referral argument: %s", context.args)

    if user_id not in user_credits:
        user_credits[user_id] = FREE_CREDITS

    credits = user_credits[user_id]

    # GPU health check
    try:
        r = requests.get(f"{GPU_API}/health", timeout=3)
        status_emoji = "🟢" if r.status_code == 200 else "🟡"
    except Exception:
        status_emoji = "🔴"

    keyboard = [
        [InlineKeyboardButton("🎨 Generate Image", callback_data='gen')],
        [InlineKeyboardButton("💎 My Credits",     callback_data='cred')],
        [InlineKeyboardButton("💰 Buy Credits",    callback_data='buy')],
        [InlineKeyboardButton("🎁 Invite Friends", callback_data='invite')],
    ]

    await update.message.reply_text(
        f"🎨 *AI Image Generator*\n\n"
        f"{status_emoji} GPU Status: L40 Powered\n"
        f"💎 *Your Credits:* {credits}\n\n"
        f"*Quality Tiers:*\n"
        f"📱 Standard (512x512) — 1 credit\n"
        f"💎 HD (1024x1024) — 3 credits\n"
        f"🔥 4K (2048x2048) — 10 credits\n\n"
        f"*Quick Start:*\n"
        f"Type any prompt: `a cool robot`\n"
        f"Or use styles: `/anime girl`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    credits = user_credits.get(user_id, 0)

    if query.data == 'gen':
        keyboard = [
            [InlineKeyboardButton("📱 Standard (1 credit)",  callback_data='quality_standard')],
            [InlineKeyboardButton("💎 HD (3 credits)",        callback_data='quality_hd')],
            [InlineKeyboardButton("🔥 4K (10 credits)",       callback_data='quality_4k')],
        ]
        await query.message.reply_text(
            f"*Choose Quality:*\n\nYour credits: {credits}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data.startswith('quality_'):
        quality = query.data.split('_', 1)[1]
        if quality not in QUALITY_TIERS:
            await query.message.reply_text("❌ Unknown quality tier.")
            return
        context.user_data['quality'] = quality
        await query.message.reply_text(
            f"*{QUALITY_TIERS[quality]['name']} Quality Selected*\n\n"
            f"Send your prompt now:\n`a futuristic robot warrior`",
            parse_mode='Markdown',
        )

    elif query.data == 'cred':
        await query.message.reply_text(
            f"💎 *Your Credits: {credits}*\n\nNeed more? /buy",
            parse_mode='Markdown',
        )

    elif query.data == 'buy':
        keyboard = [
            [InlineKeyboardButton("💎 100 Credits — $1.20",          callback_data="buy_100")],
            [InlineKeyboardButton("🔥 500 Credits — $4.80 ⭐BEST",   callback_data="buy_500")],
            [InlineKeyboardButton("⚡ 1000 Credits — $8.40",          callback_data="buy_1000")],
        ]
        await query.message.reply_text(
            f"💰 *Buy Credits = Buy Images!*\n\n"
            f"💎 $1.20 = 100 images (Standard)\n"
            f"🔥 $4.80 = 166 HD images ⭐BEST\n"
            f"⚡ $8.40 = 1000 images (Pro)\n\n"
            f"Your credits: {credits}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == 'invite':
        bot_username    = (await context.bot.get_me()).username
        invite_link     = f"https://t.me/{bot_username}?start={user_id}"
        referral_count  = user_referrals.get(user_id, 0)

        await query.message.reply_text(
            f"🎁 *Invite & Earn!*\n\n"
            f"Share your link:\n`{invite_link}`\n\n"
            f"Both you and your friend get *{REFERRAL_BONUS} bonus credits!*\n\n"
            f"Your referrals: {referral_count}",
            parse_mode='Markdown',
        )

    elif query.data.startswith('buy_'):
        packages = {
            "buy_100":  (100,  50,  "100 Credits"),
            "buy_500":  (500,  200, "500 Credits ⭐BEST"),
            "buy_1000": (1000, 350, "1000 Credits"),
        }
        if query.data not in packages:
            await query.message.reply_text("❌ Unknown package.")
            return

        credits_amount, stars, title = packages[query.data]
        await context.bot.send_invoice(
            chat_id=query.from_user.id,
            title=title,
            description=f"Get {credits_amount} credits for image generation!",
            payload=f"credits_{credits_amount}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label=f"{credits_amount} Credits", amount=stars)],
        )


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    payload = update.message.successful_payment.invoice_payload

    try:
        credits_amount = int(payload.split('_')[1])
    except (IndexError, ValueError):
        logger.error("Malformed payment payload: %s", payload)
        await update.message.reply_text("⚠️ Payment recorded but could not parse credits. Contact support.")
        return

    user_credits[user_id] = user_credits.get(user_id, 0) + credits_amount

    await update.message.reply_text(
        f"✅ *Payment Successful!*\n\n"
        f"💎 +{credits_amount} credits!\n"
        f"💰 Balance: {user_credits[user_id]}\n\n"
        f"Start generating! 🎨",
        parse_mode='Markdown',
    )
    logger.info("User %s bought %s credits", user_id, credits_amount)


async def generate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text    = update.message.text

    quality         = context.user_data.get('quality', 'standard')
    required_credits = QUALITY_TIERS[quality]['credits']

    # Parse style prefix
    style  = None
    prompt = text
    for style_name in STYLES:
        if text.startswith(f'/{style_name} '):
            style  = style_name
            prompt = text[len(f'/{style_name} '):]
            break

    # Credit check
    if user_credits.get(user_id, 0) < required_credits:
        keyboard = [[InlineKeyboardButton("💰 Buy Credits", callback_data='buy')]]
        await update.message.reply_text(
            f"❌ Need {required_credits} credits for {QUALITY_TIERS[quality]['name']}!\n"
            f"You have: {user_credits.get(user_id, 0)}",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    status = await update.message.reply_text(f"🎨 Generating {QUALITY_TIERS[quality]['name']}...")

    full_prompt = f"{prompt}, {STYLES[style]}" if style else prompt
    logger.info("User %s generating %s: %s", user_id, quality, full_prompt)

    try:
        r = requests.post(
            f"{GPU_API}/generate",
            json={"prompt": full_prompt, "size": QUALITY_TIERS[quality]['size']},
            timeout=60,
        )

        if r.status_code == 200:
            user_credits[user_id] -= required_credits
            remaining = user_credits[user_id]

            photo      = io.BytesIO(r.content)
            photo.name = 'image.png'

            await update.message.reply_photo(
                photo=photo,
                caption=(
                    f"✨ {prompt}\n"
                    f"💎 Credits: {remaining} | Quality: {QUALITY_TIERS[quality]['name']}"
                ),
            )
            await status.delete()
            logger.info("Success! User %s has %s credits remaining", user_id, remaining)
        else:
            logger.error("GPU API returned %s", r.status_code)
            await status.edit_text("❌ Generation failed. Try again!")

    except requests.exceptions.Timeout:
        await status.edit_text("⏱️ Request timed out. Try again.")
    except Exception as e:
        await status.edit_text("❌ Unexpected error. Try again.")
        logger.exception("Error generating image for user %s: %s", user_id, e)


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────
def main():
    if not _validate_env():
        sys.exit(1)

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_handler))

    logger.info("✅ Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == '__main__':
    main()
