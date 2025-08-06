# Discord TeamSpeak 3 Status Bot

Discord bot to monitor and display the status of a TeamSpeak 3 server in a Discord channel using serverquery. 

Built for single server use.

## Setup
### Docker (recommended)
Just deploy a docker image with the required config variables set.
[Docker Hub](https://hub.docker.com/r/rale2k/discord-ts3-status)
[Example compose file](./docker-compose.yml)

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
   Populate the following variables mentioned in [the config](#configuration)

4. **Run the bot:**
   ```bash
   python main.py
   ```

## Configuration
### Required
- `DISCORD_TOKEN`: Discord bot token
- `DISCORD_CHANNEL_IDS`: CSV list of Discord channel IDs
- `TS3_HOST`: TS3 server address
- `TS3_PASSWORD`: TS3 ServerQuery password

### Optional
- `TS3_QUERY_PORT`: TS3 ServerQuery port (default: 10011)
- `TS3_SERVER_PORT`: TS3 server port (default: 9987)
- `TS3_USERNAME`: TS3 ServerQuery username (default: serveradmin)
- `TS3_NICKNAME`: Bot nickname on TS (default: Discord-Bot)
- `TS3_VIRTUAL_SERVER_ID`: Virtual server ID (default: 1)
- `UPDATE_INTERVAL`: Update interval in seconds (default: 30)
- `MAX_ACTIVE_SECONDS`: Seconds before user shows as away (default: 60)
- `MAX_AWAY_SECONDS`: Seconds before user shows as idle (default: 300)
