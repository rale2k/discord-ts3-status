import logging
import os
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Config:
    discord_token: str
    discord_channel_id: int
    ts3_host: str
    ts3_query_port: int = 10011
    ts3_server_port: int = 9987
    ts3_username: str = "serveradmin"
    ts3_password: str = ""
    ts3_nickname: str = "Discord-Bot"
    ts3_virtual_server_id: int = 1
    update_interval: int = 30

    max_active_seconds: int = 60
    max_away_seconds: int = 300

    @classmethod
    def from_env(cls) -> 'Config':
        return cls(
            discord_token=os.getenv('DISCORD_TOKEN', ''),
            discord_channel_id=int(os.getenv('DISCORD_CHANNEL_ID', '0')),
            ts3_host=os.getenv('TS3_HOST', ''),
            ts3_query_port=int(os.getenv('TS3_QUERY_PORT', '10011')),
            ts3_server_port=int(os.getenv('TS3_SERVER_PORT', '9987')),
            ts3_username=os.getenv('TS3_USERNAME', 'serveradmin'),
            ts3_password=os.getenv('TS3_PASSWORD', ''),
            ts3_nickname=os.getenv('TS3_NICKNAME', 'Discord-Bot'),
            ts3_virtual_server_id=int(os.getenv('TS3_VIRTUAL_SERVER_ID', '1')),
            update_interval=int(os.getenv('UPDATE_INTERVAL', '30'))
        )
