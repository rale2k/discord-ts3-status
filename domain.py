from dataclasses import dataclass
from typing import List

@dataclass
class Client:
    nickname: str
    type: str
    flag_talking: int
    input_muted: int
    output_muted: int
    idle_time: int

    @classmethod
    def from_serverquery_response(cls, data: dict) -> 'Client':
        return cls(
            nickname=data.get('client_nickname', 'Unknown'),
            type=data.get('client_type', '0'),
            flag_talking=int(data.get('client_flag_talking', 0)),
            input_muted=int(data.get('client_input_muted', 0)),
            output_muted=int(data.get('client_output_muted', 0)),
            idle_time=int(data.get('client_idle_time', 0))
        )
    
    @property
    def is_regular_user(self) -> bool:
        return self.type == '0'
    
    @property
    def is_talking(self) -> bool:
        return bool(self.flag_talking)
    
    @property
    def is_input_muted(self) -> bool:
        return bool(self.input_muted)

    @property
    def is_output_muted(self) -> bool:
        return bool(self.output_muted)

    @property
    def idle_time_seconds(self) -> int:
        return self.idle_time // 1000

    @property
    def idle_time_formatted(self) -> str:
        idle_seconds = self.idle_time // 1000

        if idle_seconds < 60:
            return f"{idle_seconds}s"
        else:
            hours = idle_seconds // 3600
            minutes = (idle_seconds % 3600) // 60
            seconds = idle_seconds % 60
            return f"{hours}h {minutes}m {seconds}s" if hours > 0 else f"{minutes}m {seconds}s"

@dataclass
class ServerInfo:
    virtualserver_name: str
    virtualserver_maxclients: int
    virtualserver_uptime: int
    clients: List[Client]
    error: str | None = None
    
    @classmethod
    def from_serverquery_response(cls, server_data: dict, client_list: List[dict]) -> 'ServerInfo':
        users = [Client.from_serverquery_response(c) for c in client_list if c.get('client_type') == '0']
        return cls(
            virtualserver_name=server_data.get('virtualserver_name', 'Unknown'),
            virtualserver_maxclients=int(server_data.get('virtualserver_maxclients', 0)),
            virtualserver_uptime=int(server_data.get('virtualserver_uptime', 0)),
            clients=users
        )
    
    
    @classmethod
    def from_error(cls, error: str) -> 'ServerInfo':
        return cls(
            virtualserver_name="Unknown",
            virtualserver_maxclients=0,
            virtualserver_uptime=0,
            clients=[],
            error=error
        )
    
    @property
    def has_error(self) -> bool:
        return self.error is not None
    
    @property
    def errormsg(self) -> str:
        return self.error

    @property
    def name(self) -> str:
        return self.virtualserver_name
    
    @property
    def max_clients(self) -> int:
        return self.virtualserver_maxclients
    
    @property
    def uptime(self) -> int:
        return self.virtualserver_uptime
    
    @property
    def uptime_formatted(self) -> str:
        total_seconds = self.virtualserver_uptime
        weeks = total_seconds // 604800
        days = (total_seconds % 604800) // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        
        parts = []
        if weeks > 0:
            parts.append(f"{weeks}w")
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:  # Show hours if days exist
            parts.append(f"{hours}h")
        parts.append(f"{minutes}m")
        
        return " ".join(parts)
    @property
    def uptime_hours(self) -> int:
        return self.virtualserver_uptime // 3600
    
    @property
    def uptime_minutes(self) -> int:
        return (self.virtualserver_uptime % 3600) // 60
    
    @property
    def online_users_count(self) -> int:
        return len(self.clients)

    @property
    def online_users(self) -> List[Client]:
        return self.clients
