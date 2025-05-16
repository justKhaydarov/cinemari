import os
import re
import shutil
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile
from dotenv import load_dotenv
import yt_dlp

# Load the bot token from .env
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Regex patterns for Instagram and TikTok URLs
INSTAGRAM_PATTERN = r'https?://www\.instagram\.com/(p|reel)/([^/]+)/'
TIKTOK_FULL_PATTERN = r'https?://www\.tiktok\.com/(@[^/]+/video/\d+)'
TIKTOK_SHORT_PATTERN = r'https?://vt\.tiktok\.com/([a-zA-Z0-9]+)'

# Handler for /start command
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.reply("Hello! Send me an Instagram or TikTok link, and I'll download and send you the media (images or videos).")

# Handler for /help command
@dp.message(Command('help'))
async def help(message: types.Message):
    await message.reply("Send me an Instagram or TikTok link (e.g., full or short links), and I'll send you the images or videos.")

# Handler for all messages
@dp.message()
async def handle_message(message: types.Message):
    if message.entities:
        for entity in message.entities:
            if entity.type == 'url':
                url = message.text[entity.offset:entity.offset + entity.length]
                if re.match(INSTAGRAM_PATTERN, url) or re.match(TIKTOK_FULL_PATTERN, url) or re.match(TIKTOK_SHORT_PATTERN, url):
                    await handle_link(message, url)
                    return
    await message.reply("Please send a valid Instagram or TikTok link.")

# Function to download and send media
async def handle_link(message: types.Message, url: str):
    await message.reply("Downloading media, please wait...")
    download_dir = f"downloads/{message.message_id}"
    os.makedirs(download_dir, exist_ok=True)
    try:
        # Configure yt-dlp options
        ydl_opts = {
            'outtmpl': os.path.join(download_dir, '%(id)s.%(ext)s'),
            'quiet': True,
            'merge_output_format': 'mp4',  # Ensure videos are in mp4 format
            'format': 'bestvideo+bestaudio/best',  # Prefer best quality
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            files = os.listdir(download_dir)
        
        if not files:
            await message.reply("No media found for this link.")
            return
        
        # Prepare media for sending
        media = []
        for file in sorted(files):  # Sort to maintain order for carousels
            file_path = os.path.join(download_dir, file)
            if file.endswith(('.jpg', '.jpeg', '.png')):
                media.append(types.InputMediaPhoto(media=FSInputFile(file_path)))
            elif file.endswith('.mp4'):
                media.append(types.InputMediaVideo(media=FSInputFile(file_path)))
        
        # Send media based on count and type
        if media:
            if len(media) == 1:
                if isinstance(media[0], types.InputMediaPhoto):
                    await message.answer_photo(media[0].media, caption="Downloaded image")
                else:
                    await message.answer_video(media[0].media, caption="Downloaded video")
            else:
                await message.answer_media_group(media)
        else:
            await message.reply("No supported media (images or videos) found.")
    except Exception as e:
        await message.reply(f"Error downloading media: {str(e)}")
    finally:
        # Clean up downloaded files
        shutil.rmtree(download_dir, ignore_errors=True)

# Start the bot
if __name__ == '__main__':
    dp.run_polling(bot)