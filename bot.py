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

    def create_embed(self, server_info: ServerInfo) -> discord.Embed:
        if self.config.imgur_client_id:
            return self.create_image_embed(server_info)
        else:
            return self.create_textual_embed(server_info)

    def create_image_embed(self, server_info: ServerInfo) -> discord.Embed:
        # Requires config.imgur_client_id to be set
        img_buffer = None
        try:
            img_buffer = generate_status_image(server_info, self.config)
            img_buffer.seek(0)
            img_bytes = img_buffer.read()
            img_hash = hashlib.sha256(img_bytes).hexdigest()

            # reuse last uploaded image url to avoid rate limits if identical recently
            now = time.time()
            last_url = getattr(self, "_last_img_url", None)
            last_hash = getattr(self, "_last_image_hash", None)
            last_time = getattr(self, "_last_upload_time", 0)
            cache_ttl = 100
            if last_url and last_hash == img_hash and (now - last_time) < cache_ttl:
                embed = discord.Embed()
                embed.set_image(url=last_url)
                return embed

            img_base64 = base64.b64encode(img_bytes).decode('utf-8')

            headers = {
                "Authorization": f"Client-ID {self.config.imgur_client_id}"
            }
            response = requests.post(
                "https://api.imgur.com/3/image",
                headers=headers,
                data={"image": img_base64, "type": "base64"},
                timeout=15
            )

            logger.debug("imgur status: %s", response.status_code)
            logger.debug("imgur raw response: %s", response.text)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                try:
                    err = response.json()
                except Exception:
                    err = response.text
                logger.error("imgur HTTP error %s: %s", response.status_code, err)
                # try reuse cached url on rate-limit or other transient error
                if last_url:
                    embed = discord.Embed()
                    embed.set_image(url=last_url)
                    return embed
                return self.create_textual_embed(server_info)

            data = response.json()
            url = data.get("data", {}).get("link")
            if not url:
                logger.error("No link returned from imgur, response json: %s", data)
                return self.create_textual_embed(server_info)

            # cache last successful upload
            self._last_img_url = url
            self._last_image_hash = img_hash
            self._last_upload_time = time.time()

            embed = discord.Embed()
            embed.set_image(url=url)
            return embed
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload image to imgur: {e}")
            last_url = getattr(self, "_last_img_url", None)
            if last_url:
                embed = discord.Embed()
                embed.set_image(url=last_url)
                return embed
            return self.create_textual_embed(server_info)
        finally:
            if img_buffer is not None:
                try:
                    img_buffer.close()
                except Exception:
                    pass

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