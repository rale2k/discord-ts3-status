import os
from dataclasses import dataclass

@dataclass
class Config:
    discord_token: str
    discord_channel_ids: list
    discord_voice_channel_ids: list
    ts3_host: str
    timezone: str
    ts3_query_port_telnet: int = 10011
    ts3_query_port_ssh: int = 10022
    ts3_server_port: int = 9987
    ts3_username: str = "serveradmin"
    ts3_password: str = ""
    ts3_nickname: str = "Discord-Bot"
    ts3_virtual_server_id: int = 1
    update_interval: int = 70
    use_ssh: bool = True
    max_active_seconds: int = 60
    max_away_seconds: int = 300
    language: str = 'en'
    use_image_embed: bool = True

    @classmethod
    def from_env(cls) -> 'Config':
        def parse_id_list(value: str) -> list:
            if not value:
                return []
            return [int(id.strip()) for id in value.split(',') if id.strip()]

        return cls(
            discord_token=os.getenv('DISCORD_TOKEN', ''),
            discord_channel_ids=parse_id_list(os.getenv('DISCORD_CHANNEL_IDS', '')),
            discord_voice_channel_ids=parse_id_list(os.getenv('DISCORD_VOICE_CHANNEL_IDS', '')),
            ts3_host=os.getenv('TS3_HOST', ''),
            timezone=os.getenv('TIMEZONE', 'Europe/London'),
            ts3_query_port_telnet=int(os.getenv('TS3_QUERY_PORT_TELNET', '10011')),
            ts3_query_port_ssh=int(os.getenv('TS3_QUERY_PORT_SSH', '10022')),
            ts3_server_port=int(os.getenv('TS3_SERVER_PORT', '9987')),
            ts3_username=os.getenv('TS3_USERNAME', 'serveradmin'),
            ts3_password=os.getenv('TS3_PASSWORD', ''),
            ts3_nickname=os.getenv('TS3_NICKNAME', 'Discord-Bot'),
            ts3_virtual_server_id=int(os.getenv('TS3_VIRTUAL_SERVER_ID', '1')),
            update_interval=int(os.getenv('UPDATE_INTERVAL', '70')),
            use_ssh=os.getenv('USE_SSH', 'True').lower() in ('true', '1', 'yes'),
            max_active_seconds=int(os.getenv('MAX_ACTIVE_SECONDS', '60')),
            max_away_seconds=int(os.getenv('MAX_AWAY_SECONDS', '300')),
            language=os.getenv('LANGUAGE', 'en'),
            use_image_embed=os.getenv('USE_IMAGE_EMBED', 'True').lower() in ('true', '1', 'yes')
        )
