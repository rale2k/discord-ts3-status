from datetime import datetime
import logging
from typing import Optional
from config import Config
from ts3API.TS3Connection import TS3Connection
from ts3API.TS3Connection import TS3ConnectionClosedException

from domain import ServerInfo


logger = logging.getLogger(__name__)


class Teamspeak:
    def __init__(self, config: Config):
        self.config = config
        self.ts_connection: Optional[TS3Connection] = None

    def connect(self):
        try:
            if self.ts_connection:
                self.ts_connection.quit()

            query_port = self.config.ts3_query_port_ssh if self.config.use_ssh else self.config.ts3_query_port_telnet

            self.ts_connection = TS3Connection(
                host=self.config.ts3_host,
                port=query_port,
                use_ssh=self.config.use_ssh,
                username=self.config.ts3_username,
                password=self.config.ts3_password,
                accept_all_keys=True  # maybe not safe, but w/e for this simple lil' bot
            )

            self.ts_connection.login(self.config.ts3_username,
                                     self.config.ts3_password)

            self.ts_connection.use(self.config.ts3_virtual_server_id)
            logger.info("Connected to TeamSpeak server")
        except Exception as e:
            logger.error(f"Failed to connect to TeamSpeak server: {e}")
            self.ts_connection = None

    def get_server_info(self) -> ServerInfo:
        assert self.ts_connection is not None, "No server connection."

        server_info = self.ts_connection.serverinfo()
        online_clients = [
            p for p in self.ts_connection.clientlist(params=['voice', 'times']) if p.get('client_type') == '0']

        return ServerInfo.from_serverquery_response(server_info, online_clients)

    def close(self):
        if self.ts_connection:
            try:
                self.ts_connection.quit()
            except TS3ConnectionClosedException:
                pass
            self.ts_connection = None
