import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import Config
from domain import ServerInfo, Client
from image import generate_status_image

def save_test_image(server_info: ServerInfo, filename: str):
    result = generate_status_image(server_info, config=Config.from_env(), width=450)
    
    if hasattr(result, 'getvalue'):
        with open(f"docs/{filename}", "wb") as f:
            f.write(result.getvalue())
    else:
        import io
        from PIL import Image
        
        result = result.convert('RGBA')
        from image import add_rounded_corners
        result = add_rounded_corners(result, radius=12)
        
        buffer = io.BytesIO()
        result.save(buffer, 'PNG', optimize=True)
        with open(f"docs/{filename}", "wb") as f:
            f.write(buffer.getvalue())
    
    print(f"[OK] Generated: {filename}")


def test_error_state():
    server_info = ServerInfo.from_error("Connection timed out")
    save_test_image(server_info, "test_output_error_state.png")


def test_no_users_online():
    server_info = ServerInfo(
        virtualserver_name="My TeamSpeak Server",
        virtualserver_maxclients=32,
        virtualserver_uptime=86400 * 7,
        clients=[],
        error=None
    )
    save_test_image(server_info, "test_output_no_users_online.png")


def test_single_user_normal():
    client = Client(
        nickname="JohnDoe",
        type="0",
        flag_talking=0,
        input_muted=0,
        output_muted=0,
        idle_time=30000
    )
    
    server_info = ServerInfo(
        virtualserver_name="My TeamSpeak Server",
        virtualserver_maxclients=32,
        virtualserver_uptime=3600,
        clients=[client],
        error=None
    )
    save_test_image(server_info, "test_output_single_user_normal.png")


def test_single_user_talking():
    client = Client(
        nickname="ActiveSpeaker",
        type="0",
        flag_talking=1,
        input_muted=0,
        output_muted=0,
        idle_time=5000
    )
    
    server_info = ServerInfo(
        virtualserver_name="My TeamSpeak Server",
        virtualserver_maxclients=32,
        virtualserver_uptime=3600,
        clients=[client],
        error=None
    )
    save_test_image(server_info, "test_output_single_user_talking.png")


def test_single_user_input_muted():
    client = Client(
        nickname="MutedMic",
        type="0",
        flag_talking=0,
        input_muted=1,
        output_muted=0,
        idle_time=120000
    )
    
    server_info = ServerInfo(
        virtualserver_name="My TeamSpeak Server",
        virtualserver_maxclients=32,
        virtualserver_uptime=3600,
        clients=[client],
        error=None
    )
    save_test_image(server_info, "test_output_single_user_input_muted.png")


def test_single_user_output_muted():
    client = Client(
        nickname="MutedSound",
        type="0",
        flag_talking=0,
        input_muted=0,
        output_muted=1,
        idle_time=60000
    )
    
    server_info = ServerInfo(
        virtualserver_name="My TeamSpeak Server",
        virtualserver_maxclients=32,
        virtualserver_uptime=3600,
        clients=[client],
        error=None
    )
    save_test_image(server_info, "test_output_single_user_output_muted.png")


def test_multiple_users_mixed_states():
    clients = [
        Client(
            nickname="TalkingUser",
            type="0",
            flag_talking=1,
            input_muted=0,
            output_muted=0,
            idle_time=2000
        ),
        Client(
            nickname="NormalUser",
            type="0",
            flag_talking=0,
            input_muted=0,
            output_muted=0,
            idle_time=45000
        ),
        Client(
            nickname="MicMutedUser",
            type="0",
            flag_talking=0,
            input_muted=1,
            output_muted=0,
            idle_time=180000
        ),
        Client(
            nickname="SoundMutedUser",
            type="0",
            flag_talking=0,
            input_muted=0,
            output_muted=1,
            idle_time=300000
        ),
    ]
    
    server_info = ServerInfo(
        virtualserver_name="My TeamSpeak Server",
        virtualserver_maxclients=32,
        virtualserver_uptime=86400 * 3 + 3600 * 5,
        clients=clients,
        error=None
    )
    save_test_image(server_info, "test_output_multiple_users_mixed_states.png")


def test_many_users():
    clients = []
    for i in range(8):
        clients.append(Client(
            nickname=f"User{i+1}",
            type="0",
            flag_talking=1 if i == 0 else 0,
            input_muted=1 if i % 3 == 0 else 0,
            output_muted=1 if i % 4 == 0 else 0,
            idle_time=(i + 1) * 60000
        ))
    
    server_info = ServerInfo(
        virtualserver_name="Busy TeamSpeak Server",
        virtualserver_maxclients=32,
        virtualserver_uptime=604800 * 2 + 86400 * 3,
        clients=clients,
        error=None
    )
    save_test_image(server_info, "test_output_many_users.png")


def test_long_idle_times():
    clients = [
        Client(
            nickname="AFKUser1",
            type="0",
            flag_talking=0,
            input_muted=0,
            output_muted=0,
            idle_time=3600000 * 5
        ),
        Client(
            nickname="AFKUser2",
            type="0",
            flag_talking=0,
            input_muted=1,
            output_muted=0,
            idle_time=3600000 * 24
        ),
    ]
    
    server_info = ServerInfo(
        virtualserver_name="My TeamSpeak Server",
        virtualserver_maxclients=32,
        virtualserver_uptime=604800 * 4,
        clients=clients,
        error=None
    )
    save_test_image(server_info, "test_output_long_idle_times.png")


def test_short_idle_times():
    clients = [
        Client(
            nickname="VeryActiveUser",
            type="0",
            flag_talking=1,
            input_muted=0,
            output_muted=0,
            idle_time=100
        ),
        Client(
            nickname="ActiveUser2",
            type="0",
            flag_talking=0,
            input_muted=0,
            output_muted=0,
            idle_time=1500
        ),
        Client(
            nickname="ActiveUser3",
            type="0",
            flag_talking=0,
            input_muted=0,
            output_muted=0,
            idle_time=5000
        ),
    ]
    
    server_info = ServerInfo(
        virtualserver_name="My TeamSpeak Server",
        virtualserver_maxclients=32,
        virtualserver_uptime=7200,
        clients=clients,
        error=None
    )
    save_test_image(server_info, "test_output_short_idle_times.png")


def test_long_server_name():
    client = Client(
        nickname="User1",
        type="0",
        flag_talking=0,
        input_muted=0,
        output_muted=0,
        idle_time=30000
    )
    
    server_info = ServerInfo(
        virtualserver_name="Very Long TeamSpeak Server Name That Should Test Layout",
        virtualserver_maxclients=64,
        virtualserver_uptime=3600,
        clients=[client],
        error=None
    )
    save_test_image(server_info, "test_output_long_server_name.png")


def test_long_username():
    client = Client(
        nickname="VeryLongUsernameForTestingLayoutAndWrapping",
        type="0",
        flag_talking=0,
        input_muted=0,
        output_muted=0,
        idle_time=30000
    )
    
    server_info = ServerInfo(
        virtualserver_name="My TeamSpeak Server",
        virtualserver_maxclients=32,
        virtualserver_uptime=3600,
        clients=[client],
        error=None
    )
    save_test_image(server_info, "test_output_long_username.png")


def test_max_capacity():
    clients = [
        Client(
            nickname=f"User{i+1}",
            type="0",
            flag_talking=0,
            input_muted=0,
            output_muted=0,
            idle_time=60000
        )
        for i in range(10)
    ]
    
    server_info = ServerInfo(
        virtualserver_name="Full TeamSpeak Server",
        virtualserver_maxclients=10,
        virtualserver_uptime=86400,
        clients=clients,
        error=None
    )
    save_test_image(server_info, "test_output_max_capacity.png")


def test_different_error_messages():
    error_messages = [
        "Connection refused",
        "Invalid credentials",
        "Server not responding",
        "Network timeout after 30 seconds",
    ]
    
    for idx, error_msg in enumerate(error_messages):
        server_info = ServerInfo.from_error(error_msg)
        save_test_image(server_info, f"test_output_error_{idx+1}.png")


def main():
    print("=" * 60)
    print("Generating test images for discord-ts3-status bot")
    print("=" * 60)
    print()
    
    test_cases = [
        ("Error State", test_error_state),
        ("No Users Online", test_no_users_online),
        ("Single User - Normal", test_single_user_normal),
        ("Single User - Talking", test_single_user_talking),
        ("Single User - Input Muted", test_single_user_input_muted),
        ("Single User - Output Muted", test_single_user_output_muted),
        ("Multiple Users - Mixed States", test_multiple_users_mixed_states),
        ("Many Users", test_many_users),
        ("Long Idle Times", test_long_idle_times),
        ("Short Idle Times", test_short_idle_times),
        ("Long Server Name", test_long_server_name),
        ("Long Username", test_long_username),
        ("Max Capacity", test_max_capacity),
        ("Different Error Messages", test_different_error_messages),
    ]
    
    for test_name, test_func in test_cases:
        print(f"Running: {test_name}")
        try:
            test_func()
        except Exception as e:
            print(f"[FAIL] Failed: {test_name} - {e}")
    
    print()
    print("=" * 60)
    print("Test image generation complete!")
    print("Check the 'docs' folder for generated images.")
    print("=" * 60)


if __name__ == "__main__":
    main()
