from datetime import datetime
import base64
import logging
from typing import List, Optional
from zoneinfo import ZoneInfo

import discord
from discord.ext import tasks
import requests
from ts3API.utilities import TS3ConnectionClosedException
from config import Config
from domain import ServerInfo
from image import generate_status_image
from teamspeak import Teamspeak

logger = logging.getLogger(__name__)


class Bot:
    def __init__(self, config: Config):
        self.config = config
        self.message_ids: dict = {}
        self.last_image_public_id: Optional[str] = None

        self.bot = discord.Client(intents=discord.Intents.default())
        self.teamspeak: Teamspeak = Teamspeak(config)

        self.setup_events()

    def setup_events(self):
        @self.bot.event
        async def on_ready():
            logger.info(f'Bot logged in as {self.bot.user}')
            self.teamspeak.connect()
            self.update_status.start()

            self.update_status.change_interval(
                seconds=self.config.update_interval)

    def create_embed(self, server_info: ServerInfo) -> discord.Embed:
        if self.config.imgbb_api_key:
            return self.create_image_embed(server_info)
        else:
            return self.create_textual_embed(server_info)

    def create_image_embed(self, server_info: ServerInfo) -> discord.Embed:
        try:
            img_buffer = generate_status_image(server_info, self.config)
            img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')

            response = requests.post(f'https://api.imgbb.com/1/upload?expiration=21600&key={self.config.imgbb_api_key}', data={'image': img_base64}, timeout=10)

            data = response.json()
            self.last_image_public_id = data.get("public_id")

            embed = discord.Embed()
            url = data.get("data", {}).get("url")
            embed.set_image(url=url)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload image to imgbb: {e}")
            return self.create_textual_embed(server_info)
        finally:
            img_buffer.close()

        return embed

    def create_textual_embed(self, server_info: ServerInfo) -> discord.Embed:
        if server_info.has_error:
            embed = discord.Embed(
                title="⚠️ TeamSpeak Server Unavailable",
                description=f"{self.config.ts3_host}:{self.config.ts3_server_port}",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Error", value=server_info.errormsg, inline=False)
        else:
            embed = discord.Embed(
                title=f"🎤 {server_info.name}",
                color=discord.Color.green()
            )

            embed.add_field(
                name="👨‍👨‍👦‍👦 Users Online:",
                value=f"{server_info.online_users_count}/{server_info.max_clients}",
                inline=True
            )

            embed.add_field(
                name="⌚Uptime",
                value=f"{server_info.uptime_formatted}",
                inline=True
            )

            if server_info.clients:
                user_list = []
                for client in server_info.clients:
                    if client.idle_time_seconds < self.config.max_active_seconds:
                        status_icon = "🟢"
                    elif client.idle_time_seconds < self.config.max_away_seconds:
                        status_icon = "🟡"
                    else:
                        status_icon = "🔴"

                    user_list.append(
                        f"{status_icon} **{client.nickname}** (*{client.idle_time_formatted}* ago)")

                embed.add_field(
                    name="👥 Users (last active):",
                    value="\n".join(user_list) if user_list else "None",
                    inline=False
                )

        embed.timestamp = datetime.now(tz=ZoneInfo(self.config.timezone))
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
                status = self.teamspeak.get_server_info()
            except (TS3ConnectionClosedException, Exception) as e:
                error_msg = "Teamspeak connection closed" if isinstance(
                    e, TS3ConnectionClosedException) else str(e)
                logger.error(f"{error_msg}. Reconnecting...")
                status = ServerInfo.from_error('No connection to server!')
                self.teamspeak.connect()

            embed = self.create_embed(status)
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
                    await channel.purge(limit=100, check=lambda m: m.author == self.bot.user)
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
        if self.teamspeak:
            self.teamspeak.close()
        await self.bot.close()
