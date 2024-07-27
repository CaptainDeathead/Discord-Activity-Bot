# Discord-Activity-Bot
A Discord bot that tracks users time spent online in Discord and their rich presence

## About
This bot provides insights into peoples activity on Discord.

It watches how much time they spend online, idle, do not disturb and offline.
It also watches peoples rich presence, so it can provide information on how much time they spend online, idle and do not disturb for each presence.

### Why is this useful?
Some people like to know how much they spend doing different things like playing games, programming and whatever else they do while on Discord.

Wheather it be productivity or just for fun, people like this stuff, so here it is!

## Installation
### Adding to a server
To add the bot to your Discord server use this link: https://discord.com/oauth2/authorize?client_id=1264863020316626944

### Running from your machine
To host it yourself:

1. Make a bot on [Discord Devolpers Portal](https://discord.com/developers/applications) and copy the token.
2. Give the bot scope permissions for `applications.commands`, `bot` and permissions for `Read Message History`, `Send Messages`, `Use Slash Commands` and `View Channels`
3. Clone the repo and make a file called 'token.txt' in the bot's folder
4. Paste your bot's token into token.txt
5. Install the required packages by entering this command in your terminal in the bots folder: `pip install -r requirements.txt`
6. Add the bot to your server using the link on your portal and run `python3 main.py`
7. Type '`/help`' to get started and enjoy!