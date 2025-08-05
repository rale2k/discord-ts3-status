from datetime import datetime
from typing import Optional

import discord
from discord.ext import tasks
from ts3API.TS3Connection import TS3Connection

from config import Config, logger


class TS3Bot:
    def __init__(self, config: Config):
        self.config = config
        self.bot = discord.Client(intents=discord.Intents.default())
        self.ts3_conn: Optional[TS3Connection] = None
        self.message_id: Optional[int] = None

        self.setup_events()

    def setup_events(self):
        @self.bot.event
        async def on_ready():
            logger.info(f'Bot logged in as {self.bot.user}')
            self.connect_ts3()
            self.update_status.start()

    def connect_ts3(self):
        try:
            if self.ts3_conn:
                try:
                    self.ts3_conn.quit()
                except:
                    pass

            self.ts3_conn = TS3Connection(
                self.config.ts3_host, self.config.ts3_query_port)
            self.ts3_conn.login(self.config.ts3_username,
                                self.config.ts3_password)
            self.ts3_conn.use(self.config.ts3_virtual_server_id)
            logger.info("Connected to TeamSpeak 3 server")
        except Exception as e:
            logger.error(f"Failed to connect to TeamSpeak 3: {e}")
            self.ts3_conn = None

    def get_server_status(self) -> dict:
        if not self.ts3_conn:
            return {"error": "Not connected to TeamSpeak server"}

        try:
            server_info = self.ts3_conn.serverinfo()
            client_list = self.ts3_conn.clientlist()

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
        except Exception as e:
            logger.error(f"Error getting server status: {e}")
            return {"error": str(e)}

    def get_client_status(self, client_id) -> dict:
        if not self.ts3_conn:
            return {"error": "Not connected to TeamSpeak server"}
        try:
            return self.ts3_conn.clientinfo(client_id)
        except Exception as e:
            logger.error(
                f"Error getting client info for client with id: {client_id}")
            return {"error": str(e)}

    def format_status_message(self, status: dict) -> discord.Embed:
        if "error" in status:
            embed = discord.Embed(
                title="TeamSpeak Server Status",
                description="**Server Offline or unreachable**",
                color=discord.Color.red()
            )
            embed.add_field(name="Error", value=status["error"], inline=False)
        else:
            embed = discord.Embed(
                title=f"<:TeamSpeak:1402388799396384859> {status['server_name']}",
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

                    if idle_seconds < Config.max_active_seconds:
                        status_icon = "🟢"
                    elif idle_seconds < Config.max_away_seconds:
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

    @tasks.loop(seconds=30)
    async def update_status(self):
        try:
            channel = self.bot.get_channel(self.config.discord_channel_id)
            if not channel:
                logger.error(
                    f"Discord channel with ${self.config.discord_channel_id} not found")
                return

            status = self.get_server_status()

            if "error" in status and not self.ts3_conn:
                logger.info("Reconnecting to TS server...")
                await self.connect_ts3()
                status = self.get_server_status()

            embed = self.format_status_message(status)

            if self.message_id:
                try:
                    message = await channel.fetch_message(self.message_id)
                    await message.edit(embed=embed)
                except (discord.NotFound, discord.HTTPException):
                    message = await channel.send(embed=embed)
                    self.message_id = message.id
            else:
                await channel.purge()
                message = await channel.send(embed=embed)
                self.message_id = message.id

        except Exception as e:
            logger.error(f"Error updating status: {e}")

    @update_status.before_loop
    async def before_update_status(self):
        await self.bot.wait_until_ready()

    async def run(self):
        await self.bot.start(self.config.discord_token)

    async def close(self):
        if self.ts3_conn:
            self.ts3_conn.quit()
        await self.bot.close()
