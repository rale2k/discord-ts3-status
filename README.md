# Discord TeamSpeak 3 Status Bot

Discord bot to monitor and display the status of a TeamSpeak 3 server in a Discord channel. 

Built for single server use.

## Setup
### Locally 
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Configure the bot:**
   Populate the following variables mentioned in [the config](#my-multi-word-header)

4. **Run the bot:**
   ```bash
   python main.py
   ```

## Configuration
### Required
- `DISCORD_TOKEN`: Discord bot token
- `DISCORD_CHANNEL_ID`: Discord channel ID (enable Developer Mode in Discord to copy channel ID)
- `TS3_HOST`: TeamSpeak 3 server address
- `TS3_PASSWORD`: ServerQuery password

### Optional
- `TS3_QUERY_PORT`: ServerQuery port (default: 10011)
- `TS3_SERVER_PORT`: TeamSpeak server port (default: 9987)
- `TS3_USERNAME`: ServerQuery username (default: serveradmin)
- `TS3_NICKNAME`: Bot nickname on TS3 (default: Discord-Bot)
- `TS3_VIRTUAL_SERVER_ID`: Virtual server ID (default: 1)
- `UPDATE_INTERVAL`: Update interval in seconds (default: 30)
