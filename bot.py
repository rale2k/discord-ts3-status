from datetime import datetime
import logging
from typing import List, Optional

import discord
from discord.ext import tasks
from ts3API.TS3Connection import TS3Connection
from ts3API.utilities import TS3ConnectionClosedException
from config import Config


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TSBot:
    def __init__(self, config: Config):
        self.config = config
        self.bot = discord.Client(intents=discord.Intents.default())
        self.ts_connection: Optional[TS3Connection] = None
        self.message_ids: dict = {}

        self.setup_events()

    def setup_events(self):
        @self.bot.event
        async def on_ready():
            logger.info(f'Bot logged in as {self.bot.user}')
            self.connect_ts3()
            self.update_status.start()

            self.update_status.change_interval(
                seconds=self.config.update_interval)

    def connect_ts3(self):
        try:
            if self.ts_connection:
                try:
                    self.ts_connection.quit()
                except:
                    pass

            query_port = self.config.ts3_query_port_ssh if self.config.use_ssh else self.config.ts3_query_port_telnet

            self.ts_connection = TS3Connection(
                host=self.config.ts3_host,
                port=query_port,
                use_ssh=self.config.use_ssh,
                username=self.config.ts3_username,
                password=self.config.ts3_password,
                accept_all_keys=True  # not safe, but w/e for this simple lil' bot
            )

            self.ts_connection.login(self.config.ts3_username,
                                self.config.ts3_password)

            self.ts_connection.use(self.config.ts3_virtual_server_id)
            logger.info("Connected to TeamSpeak server")
        except Exception as e:
            logger.error(f"Failed to connect to TeamSpeak server: {e}")
            self.ts_connection = None

    def get_server_status(self) -> dict:
        assert self.ts_connection is not None, "No server connection."

        server_info = self.ts_connection.serverinfo()
        client_list = self.ts_connection.clientlist()

        online_clients = []
        for client in client_list:
            if client.get('client_type') == '0':
                client_info = self.get_client_status(client.get("clid"))
                if "error" not in client_info:
                    online_clients.append(client_info)

        return {
            "server_name": server_info.get('virtualserver_name', 'Unknown'),
            "online_users": len(online_clients),
            "max_clients": int(server_info.get('virtualserver_maxclients', 0)),
            "uptime": int(server_info.get('virtualserver_uptime', 0)),
            "clients": online_clients,
            "last_updated": datetime.now()
        }

    def get_client_status(self, client_id) -> dict:
        return self.ts_connection.clientinfo(client_id)

    def format_status_message(self, status: dict) -> discord.Embed:
        if "error" in status:
            embed = discord.Embed(
                title="⚠️ TeamSpeak Server Unavailable",
                description=f"{self.config.ts3_host}:{self.config.ts3_server_port}",
                color=discord.Color.red()
            )
            embed.add_field(name="Error", value=status["error"], inline=False)
        else:
            embed = discord.Embed(
                title=f"🎤 {status['server_name']}",
                color=discord.Color.green()
            )

            embed.add_field(
                name="👨‍👨‍👦‍👦 Users Online:",
                value=f"{status['online_users']}/{status['max_clients']}",
                inline=True
            )

            uptime_hours = status['uptime'] // 3600
            uptime_minutes = (status['uptime'] % 3600) // 60
            embed.add_field(
                name="⌚Uptime",
                value=f"{uptime_hours}h {uptime_minutes}m",
                inline=True
            )

            if status['clients']:
                user_list = []
                for client in status['clients']:
                    nickname = client.get('client_nickname', 'Unknown')
                    idle_time_ms = int(client.get('client_idle_time', 0))
                    idle_seconds = idle_time_ms // 1000

                    if idle_seconds < 60:
                        idle_str = f"{idle_seconds}s"
                    else:
                        minutes = idle_seconds // 60
                        seconds = idle_seconds % 60
                        idle_str = f"{minutes}m {seconds}s"

                    if idle_seconds < self.config.max_active_seconds:
                        status_icon = "🟢"
                    elif idle_seconds < self.config.max_away_seconds:
                        status_icon = "🟡"
                    else:
                        status_icon = "🔴"

                    user_list.append(
                        f"{status_icon} **{nickname}** (*{idle_str}* ago)")

                embed.add_field(
                    name="👥 Users (last active):",
                    value="\n".join(user_list) if user_list else "None",
                    inline=False
                )

        embed.timestamp = status.get('last_updated', datetime.now())
        return embed

    async def get_channels(self) -> List[Optional[discord.TextChannel]]:
        channels = []
        for id in self.config.discord_channel_ids:
            channel = self.bot.get_channel(id)
            if not channel:
                logger.warning(
                    f"Discord channel with id {id} not found")
                self.message_ids.pop(f"{id}", None)
                continue
            channels.append(channel)
        return channels

    @tasks.loop(seconds=30)
    async def update_status(self):
        try:
            channels = await self.get_channels()

            try:
                status = self.get_server_status()
            except (TS3ConnectionClosedException, Exception) as e:
                error_msg = "Teamspeak connection closed" if isinstance(
                    e, TS3ConnectionClosedException) else str(e)
                logger.error(f"{error_msg}. Reconnecting...")
                status = {"error": "No connection to server!"}
                self.connect_ts3()

            embed = self.format_status_message(status)
            for channel in channels:
                message_id = self.message_ids.get(f"{channel.id}")
                if message_id is not None:
                    try:
                        message = await channel.fetch_message(int(message_id))
                        await message.edit(embed=embed)
                    except (discord.NotFound):
                        message = await channel.send(embed=embed)
                        self.message_ids.update(
                            {f"{channel.id}": f"{message.id}"})
                else:
                    await channel.purge()
                    message = await channel.send(embed=embed)
                    self.message_ids.update({f"{channel.id}": f"{message.id}"})

        except Exception as e:
            logger.error(f"Error updating status: {e}")

    @update_status.before_loop
    async def before_update_status(self):
        await self.bot.wait_until_ready()

    async def run(self):
        await self.bot.start(self.config.discord_token)

    async def close(self):
        if self.ts_connection:
            self.ts_connection.quit()
        await self.bot.close()
