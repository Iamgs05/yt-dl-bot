


import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import tempfile

TOKEN = os.environ.get("8613468671:AAFLxqutr5zyHRZtnV837EVaxqG8x8csvR8")
user_links = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to YT & Instagram Downloader!\n\n"
        "Just send me any:\n"
        "🎥 YouTube link\n"
        "📸 Instagram link\n\n"
        "I'll give you download options!"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_id = update.message.from_user.id

    is_yt = "youtube.com" in url or "youtu.be" in url
    is_ig = "instagram.com" in url

    if not is_yt and not is_ig:
        await update.message.reply_text("❌ Send a valid YouTube or Instagram link!")
        return

    user_links[user_id] = url
    msg = await update.message.reply_text("⏳ Fetching info...")

    try:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')[:50]

        if is_ig:
            keyboard = [
                [InlineKeyboardButton("🎥 Video (Best)", callback_data="video_best")],
                [InlineKeyboardButton("🎵 Audio MP3", callback_data="audio_mp3")],
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("🎥 360p", callback_data="video_360")],
                [InlineKeyboardButton("🎥 720p", callback_data="video_720")],
                [InlineKeyboardButton("🎥 1080p", callback_data="video_1080")],
                [InlineKeyboardButton("🎵 Audio MP3", callback_data="audio_mp3")],
            ]

        await msg.edit_text(
            f"🎬 *{title}*\n\nChoose format:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        await msg.edit_text(f"❌ Could not fetch video.\n`{str(e)[:200]}`", parse_mode='Markdown')

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    choice = query.data

    if user_id not in user_links:
        await query.edit_message_text("❌ Session expired. Send the link again.")
        return

    url = user_links[user_id]
    await query.edit_message_text("⬇️ Downloading... please wait!")

    format_map = {
        "audio_mp3": {
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        },
        "video_360": {
            'format': 'bestvideo[height<=360]+bestaudio/best',
            'merge_output_format': 'mp4'
        },
        "video_720": {
            'format': 'bestvideo[height<=720]+bestaudio/best',
            'merge_output_format': 'mp4'
        },
        "video_1080": {
            'format': 'bestvideo[height<=1080]+bestaudio/best',
            'merge_output_format': 'mp4'
        },
        "video_best": {
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4'
        },
    }

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                **format_map[choice],
                'outtmpl': f'{tmpdir}/%(title)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            files = os.listdir(tmpdir)
            if not files:
                await query.edit_message_text("❌ Download failed. Try again.")
                return

            filepath = os.path.join(tmpdir, files[0])
            filesize = os.path.getsize(filepath) / (1024 * 1024)

            if filesize > 50:
                await query.edit_message_text(
                    f"❌ File too large ({filesize:.1f}MB). Telegram max is 50MB. Try lower quality."
                )
                return

            await query.edit_message_text("📤 Uploading to Telegram...")

            with open(filepath, 'rb') as f:
                if choice == "audio_mp3":
                    await context.bot.send_audio(
                        chat_id=query.message.chat_id,
                        audio=f,
                        caption="🎵 Here's your audio! Enjoy 🎶"
                    )
                else:
                    await context.bot.send_video(
                        chat_id=query.message.chat_id,
                        video=f,
                        caption="🎥 Here's your video! Enjoy 🎉",
                        supports_streaming=True
                    )

            await query.edit_message_text("✅ Done! Enjoy 🎉")
            del user_links[user_id]

    except Exception as e:
        await query.edit_message_text(f"❌ Failed: `{str(e)[:200]}`", parse_mode='Markdown')

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable not set!")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(CallbackQueryHandler(handle_button))
    print("🤖 Bot is running!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
