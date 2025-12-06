async def generate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    
    style = ""
    if text.startswith('/'):
        parts = text.split(' ', 1)
        if len(parts) == 2:
            style = parts[0][1:]
            prompt = parts[1]
        else:
            await update.message.reply_text("Usage: `/pfp your prompt`", parse_mode='Markdown')
            return
    else:
        prompt = text
    
    if user_credits.get(user_id, 0) < 1:
        await update.message.reply_text("❌ No credits! Use /start")
        return
    
    prompts = [p.strip() for p in prompt.split('\n') if p.strip()]
    if user_credits.get(user_id, 0) < len(prompts):
        await update.message.reply_text(f"Need {len(prompts)} credits, have {user_credits[user_id]}")
        return
    
    status = await update.message.reply_text(f"🎨 Generating {len(prompts)} image(s)...")
    
    success = 0
    for i, p in enumerate(prompts):
        try:
            logger.info(f"Requesting: {p[:50]}")
            
            r = requests.post(
                f"{GPU_API}/generate",
                json={"prompt": p, "style": style},
                timeout=30,
                stream=True
            )
            
            logger.info(f"Response status: {r.status_code}")
            
            if r.status_code == 200:
                photo = io.BytesIO(r.content)
                photo.name = 'image.png'
                
                logger.info(f"Sending photo to user {user_id}")
                
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"✨ {p[:80]}"
                )
                
                success += 1
                logger.info(f"✅ Sent image {i+1}")
            else:
                logger.error(f"GPU API returned {r.status_code}")
                await update.message.reply_text(f"❌ Generation {i+1} failed (GPU error)")
                
        except requests.exceptions.Timeout:
            logger.error("Timeout connecting to GPU")
            await update.message.reply_text(f"⏱️ Image {i+1} timed out")
        except Exception as e:
            logger.error(f"Error on image {i+1}: {e}")
            await update.message.reply_text(f"❌ Image {i+1} failed: {str(e)[:100]}")
    
    user_credits[user_id] -= success
    remaining = user_credits[user_id]
    
    await update.message.reply_text(
        f"✅ Done! 💎 Left: {remaining}"
    )
    
    try:
        await status.delete()
    except:
        pass
