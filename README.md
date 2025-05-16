Telegram Media Downloader Bot
This Telegram bot allows users to download media from Instagram and TikTok by sending links to the bot. It supports various types of links and can handle images, videos, and carousels. Additionally, the bot can be configured to require users to join a specific Telegram channel to use its features.
Features

Media Downloading: Supports downloading images, videos, and carousels from Instagram and TikTok.
Channel Requirement: Optionally require users to join a specific Telegram channel to use the bot.
Admin Controls: Admins can set or remove the required channel using commands.
User-Friendly: Provides clear instructions and inline buttons for easy channel joining.

Prerequisites

Python 3.8 or higher
Telegram bot token from @BotFather
Optional: ffmpeg installed for better media quality and smaller file sizes

Setup Instructions

Clone the repository:git clone https://github.com/justKhaydarov/cinemari.git


Navigate to the project directory:cd cinemari


Install dependencies:pip install aiogram yt-dlp python-dotenv


Create a .env file with your bot token:echo "BOT_TOKEN=your_bot_token_here" > .env


Run the bot:python bot.py


Usage

Start the bot: Send /start to receive a welcome message and instructions.
Send links: Send Instagram or TikTok links to download media.
Channel requirement: If set, users must join the specified channel to use the bot. The bot will prompt non-members with a "Join Channel" button or instructions.

Admin Features
set ADMIN_USER_ID to an actual telegram_user_id to set an admin
Set required channel: Use /setchannel <channel_identifier> (e.g., @MyChannel or channel ID).
Remove channel requirement: Use /removechannel.
Note: The bot must be an administrator in the channel to check user memberships.

Known Issues
Private content: The bot cannot download private Instagram or TikTok posts.

Contributing
Feel free to open issues or submit pull requests to improve the bot. Contributions are welcome!
