import os
import re
import shutil
import json
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import FSInputFile
from dotenv import load_dotenv
import yt_dlp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the bot token from .env
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Define the admin user ID (replace with your actual admin user ID)
ADMIN_USER_ID = 7965709229  # TODO: Replace with your actual Telegram user ID

# Regex patterns for Instagram and TikTok URLs
INSTAGRAM_PATTERN = r'https?://www\.instagram\.com/(p|reel)/([^/]+)/'
TIKTOK_FULL_PATTERN = r'https?://www\.tiktok\.com/(@[^/]+/video/\d+)'
TIKTOK_SHORT_PATTERN = r'https?://vt\.tiktok\.com/([a-zA-Z0-9]+)'

# Global config variable to store channel details
config = None

# Asynchronous functions to load and save config
async def load_config():
    loop = asyncio.get_event_loop()
    try:
        with open('config.json', 'r') as f:
            return await loop.run_in_executor(None, json.load, f)
    except FileNotFoundError:
        return {"channel_id": None, "channel_title": None, "channel_username": None}

async def save_config(config):
    loop = asyncio.get_event_loop()
    with open('config.json', 'w') as f:
        await loop.run_in_executor(None, json.dump, config, f)

# Startup function to load config
async def on_startup():
    global config
    config = await load_config()
    logger.info(f"Config loaded: {config}")

dp.startup.register(on_startup)

# Handler for /start command
@dp.message(CommandStart())
async def start(message: types.Message):
    reply = "Hello! Send me an Instagram or TikTok link, and I'll download and send you the media."
    if config['channel_id'] is not None and message.from_user.id != ADMIN_USER_ID:
        try:
            member = await bot.get_chat_member(config['channel_id'], message.from_user.id)
            logger.info(f"User {message.from_user.id} membership status: {member.status}")
            if member.status not in ['member', 'administrator', 'creator']:
                # User is not a member, add join prompt
                if config['channel_username']:
                    reply += "\n\nTo use this bot, you must join the channel:"
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="Join Channel", url=f"https://t.me/{config['channel_username']}")]
                    ])
                    await message.reply(reply, reply_markup=keyboard)
                else:
                    reply += f"\n\nTo use this bot, you must join the channel: {config['channel_title']} (ID: {config['channel_id']}). Please contact the admin for an invite link."
                    await message.reply(reply)
                return
        except Exception as e:
            logger.error(f"Membership check failed for user {message.from_user.id}: {e}")
            # Assume user is not a member if check fails
            if config['channel_username']:
                reply += "\n\nTo use this bot, you must join the channel:"
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Join Channel", url=f"https://t.me/{config['channel_username']}")]
                ])
                await message.reply(reply, reply_markup=keyboard)
            else:
                reply += f"\n\nTo use this bot, you must join the channel: {config['channel_title']} (ID: {config['channel_id']}). Please contact the admin for an invite link."
                await message.reply(reply)
            return
    # User is admin, or is a member, or no channel is set
    await message.reply(reply)

# Handler for /help command
@dp.message(Command('help'))
async def help_command(message: types.Message):
    reply = "Send me an Instagram or TikTok link, and I'll download and send you the media."
    if config['channel_id'] is not None and message.from_user.id != ADMIN_USER_ID:
        try:
            member = await bot.get_chat_member(config['channel_id'], message.from_user.id)
            logger.info(f"User {message.from_user.id} membership status: {member.status}")
            if member.status not in ['member', 'administrator', 'creator']:
                if config['channel_username']:
                    reply += "\n\nTo use this bot, you must join the channel:"
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="Join Channel", url=f"https://t.me/{config['channel_username']}")]
                    ])
                    await message.reply(reply, reply_markup=keyboard)
                else:
                    reply += f"\n\nTo use this bot, you must join the channel: {config['channel_title']} (ID: {config['channel_id']}). Please contact the admin for an invite link."
                    await message.reply(reply)
                return
        except Exception as e:
            logger.error(f"Membership check failed for user {message.from_user.id}: {e}")
            if config['channel_username']:
                reply += "\n\nTo use this bot, you must join the channel:"
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Join Channel", url=f"https://t.me/{config['channel_username']}")]
                ])
                await message.reply(reply, reply_markup=keyboard)
            else:
                reply += f"\n\nTo use this bot, you must join the channel: {config['channel_title']} (ID: {config['channel_id']}). Please contact the admin for an invite link."
                await message.reply(reply)
            return
    await message.reply(reply)

# Handler for /setchannel command (admin only)
@dp.message(Command('setchannel'))
async def set_channel(message: types.Message):
    if message.from_user.id != ADMIN_USER_ID:
        await message.reply("You are not authorized to use this command.")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Please provide the channel username or ID.")
        return
    channel_identifier = args[1]
    try:
        chat = await bot.get_chat(channel_identifier)
        if chat.type != 'channel':
            await message.reply("The provided chat is not a channel.")
            return
        chat_id = chat.id
        bot_member = await bot.get_chat_member(chat_id, bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await message.reply("The bot must be an administrator in the channel to check memberships.")
            return
        config['channel_id'] = chat_id
        config['channel_title'] = chat.title
        config['channel_username'] = chat.username if chat.username else None
        await save_config(config)
        await message.reply(f"Channel set to {chat.title} ({chat_id}). Users must join this channel to use the bot.")
    except Exception as e:
        await message.reply(f"Error setting channel: {e}")

# Handler for /removechannel command (admin only)
@dp.message(Command('removechannel'))
async def remove_channel(message: types.Message):
    if message.from_user.id != ADMIN_USER_ID:
        await message.reply("You are not authorized to use this command.")
        return
    config['channel_id'] = None
    config['channel_title'] = None
    config['channel_username'] = None
    await save_config(config)
    await message.reply("Channel requirement removed. Users can now use the bot without joining a channel.")

# Handler for all messages
@dp.message()
async def handle_message(message: types.Message):
    if message.from_user.id != ADMIN_USER_ID and config['channel_id'] is not None:
        try:
            member = await bot.get_chat_member(config['channel_id'], message.from_user.id)
            logger.info(f"User {message.from_user.id} membership status: {member.status}")
            if member.status not in ['member', 'administrator', 'creator']:
                if config['channel_username']:
                    reply = f"To use this bot, you must join the channel:"
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="Join Channel", url=f"https://t.me/{config['channel_username']}")]
                    ])
                    await message.reply(reply, reply_markup=keyboard)
                else:
                    await message.reply(f"To use this bot, you must join the channel: {config['channel_title']} (ID: {config['channel_id']}). Please contact the admin for an invite link.")
                return
        except Exception as e:
            logger.error(f"Membership check failed for user {message.from_user.id}: {e}")
            await message.reply(f"Error checking channel membership: {e}")
            return
    # Proceed with link handling
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
            'merge_output_format': 'mp4',
            'format': 'bestvideo+bestaudio/best',
        }
        # Add cookies if cookies.txt exists
        cookies_file = 'cookies.txt'
        if os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            files = os.listdir(download_dir)
        
        if not files:
            await message.reply("No media found for this link.")
            return
        
        # Prepare media for sending
        media = []
        for file in sorted(files):
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
        error_message = str(e)
        reply = f"Error downloading media: {error_message}"
        if "Restricted Video" in error_message or "not available in your country" in error_message:
            reply += "\nThis content may be geo-restricted. Try using a VPN or ensure cookies.txt is provided with a logged-in Instagram session."
        await message.reply(reply)
    finally:
        # Clean up downloaded files
        shutil.rmtree(download_dir, ignore_errors=True)

# Start the bot
if __name__ == '__main__':
    dp.run_polling(bot)