from datetime import datetime
import base64
import logging
import hashlib
import time
from typing import List, Optional
from zoneinfo import ZoneInfo

import discord
from discord.ext import tasks
import requests
from ts3API.utilities import TS3ConnectionClosedException
from config import Config
from domain import ServerInfo
from i18n import get_translator
from image import generate_status_image
from teamspeak import Teamspeak

logger = logging.getLogger(__name__)

class Bot:
    def __init__(self, config: Config):
        self.config = config
        self.message_ids: dict = {}

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

    def create_embed(self, server_info: ServerInfo) -> tuple[discord.Embed, Optional[discord.File]]:
        if self.config.use_image_embed:
            return self.create_image_embed(server_info)
        else:
            return self.create_textual_embed(server_info), None

    def create_image_embed(self, server_info: ServerInfo) -> tuple[discord.Embed, Optional[discord.File]]:
        img_buffer = None
        try:
            img_buffer = generate_status_image(server_info, self.config)
            img_buffer.seek(0)

            file = discord.File(img_buffer, filename="status.png")

            embed = discord.Embed(color=discord.Color.green())
            embed.set_image(url="attachment://status.png")
            
            return embed, file
            
        except Exception as e:
            logger.error(f"Failed to generate status image: {e}")
            return self.create_textual_embed(server_info), None
        finally:
            if img_buffer is not None:
                img_buffer.close()

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

    async def get_voice_channels(self) -> List[Optional[discord.VoiceChannel]]:
        channels = []
        for id in getattr(self.config, "discord_voice_channel_ids", []):
            channel = self.bot.get_channel(id)
            if not channel:
                logger.warning(f"Discord voice channel with id {id} not found")
                continue
            if getattr(channel, "type", None) != discord.ChannelType.voice:
                logger.warning(f"Channel {id} is not a voice channel (type={channel.type})")
                continue
            channels.append(channel)
        return channels

    async def update_voice_channel_count(self, server_info: ServerInfo, channels: List[discord.VoiceChannel]):
        if not channels:
            return

        template = getattr(self.config, "discord_voice_channel_name_template", "Na Teamspeaku: {count}")
        new_name = template.format(count=server_info.online_users_count, max=server_info.max_clients)

        for channel in channels:
            if not channel:
                continue
            if channel.name == new_name:
                continue
            try:
                await channel.edit(name=new_name)
                logger.info(f"Updated voice channel name for {channel.id} -> {new_name}")
            except discord.Forbidden:
                logger.warning(f"No permission to rename channel {channel.id}")
            except Exception as e:
                logger.error(f"Failed to update channel name {channel.id}: {e}")

    @tasks.loop(seconds=30)
    async def update_status(self):
        try:
            channels = await self.get_channels()
            voice_channels = await self.get_voice_channels()
            try:
                status = self.teamspeak.get_server_info()
            except (TS3ConnectionClosedException, Exception) as e:
                logger.error(f"Error getting server info: {e}")
                self.teamspeak.connect()

            embed, file = self.create_embed(status)
            
            for channel in channels:
                if not channel:
                    continue
                    
                message_id = self.message_ids.get(channel.id)
                try:
                    if message_id:
                        try:
                            message = await channel.fetch_message(message_id)
                            await message.edit(embed=embed, attachments=[file] if file else [])
                        except discord.NotFound:
                            msg = await channel.send(embed=embed, file=file)
                            self.message_ids[channel.id] = msg.id
                    else:
                        await channel.purge(limit=100, check=lambda m: m.author == self.bot.user)
                        msg = await channel.send(embed=embed, file=file)
                        self.message_ids[channel.id] = msg.id
                except Exception as e:
                    logger.error(f"Error updating channel {channel.id}: {e}")

            if voice_channels:
                await self.update_voice_channel_count(status, voice_channels)

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
