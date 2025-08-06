import asyncio

from bot import TS3Bot
from config import Config, logger


async def main():
    config = Config.from_env()

    if not config.discord_token:
        logger.error("DISCORD_TOKEN not set")
        return

    if not config.discord_channel_ids:
        logger.error("DISCORD_CHANNEL_ID not set")
        return

    if not config.ts3_host:
        logger.error("TS3_HOST not set")
        return

    bot = TS3Bot(config)

    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
