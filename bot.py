import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import asyncio
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

    if "youtube.com" not in url and "youtu.be" not in url and "instagram.com" not in url:
        await update.message.reply_text("❌ Please send a valid YouTube or Instagram link!")
        return

    user_links[user_id] = url
    await update.message.reply_text("⏳ Fetching info...")

    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')[:50]

        keyboard = []

        if "instagram.com" in url:
            keyboard = [
                [InlineKeyboardButton("🎥 Video (Best)", callback_data=f"video_best")],
                [InlineKeyboardButton("🎵 Audio MP3", callback_data=f"audio_mp3")],
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("🎥 Video 360p", callback_data="video_360")],
                [InlineKeyboardButton("🎥 Video 720p", callback_data="video_720")],
                [InlineKeyboardButton("🎥 Video 1080p", callback_data="video_1080")],
                [InlineKeyboardButton("🎵 Audio MP3", callback_data="audio_mp3")],
            ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"🎬 *{title}*\n\nChoose download format:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching video info. Try another link.\n`{str(e)[:100]}`", parse_mode='Markdown')

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

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            if choice == "audio_mp3":
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': f'{tmpdir}/%(title)s.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'quiet': True,
                }
            elif choice == "video_360":
                ydl_opts = {
                    'format': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
                    'outtmpl': f'{tmpdir}/%(title)s.%(ext)s',
                    'merge_output_format': 'mp4',
                    'quiet': True,
                }
            elif choice == "video_720":
                ydl_opts = {
                    'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                    'outtmpl': f'{tmpdir}/%(title)s.%(ext)s',
                    'merge_output_format': 'mp4',
                    'quiet': True,
                }
            elif choice == "video_1080":
                ydl_opts = {
                    'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
                    'outtmpl': f'{tmpdir}/%(title)s.%(ext)s',
                    'merge_output_format': 'mp4',
                    'quiet': True,
                }
            elif choice == "video_best":
                ydl_opts = {
                    'format': 'bestvideo+bestaudio/best',
                    'outtmpl': f'{tmpdir}/%(title)s.%(ext)s',
                    'merge_output_format': 'mp4',
                    'quiet': True,
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
                await query.edit_message_text(f"❌ File too large ({filesize:.1f}MB). Telegram limit is 50MB. Try lower quality.")
                return

            await query.edit_message_text("📤 Uploading to Telegram...")

            with open(filepath, 'rb') as f:
                if choice == "audio_mp3":
                    await context.bot.send_audio(
                        chat_id=query.message.chat_id,
                        audio=f,
                        caption="🎵 Here's your audio!"
                    )
                else:
                    await context.bot.send_video(
                        chat_id=query.message.chat_id,
                        video=f,
                        caption="🎥 Here's your video!",
                        supports_streaming=True
                    )

            await query.edit_message_text("✅ Done! Enjoy 🎉")
            del user_links[user_id]

    except Exception as e:
        await query.edit_message_text(f"❌ Failed: `{str(e)[:150]}`", parse_mode='Markdown')

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(CallbackQueryHandler(handle_button))
    print("🤖 Bot is running!")
    app.run_polling()

if __name__ == "__main__":
    main()
