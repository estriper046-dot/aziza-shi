"""Entry point. Start the bot with:  python run.py"""
import asyncio
import logging
import sys

from pydantic import ValidationError


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        from bot.app import run_bot
    except ValidationError as error:
        # Settings are read from .env when bot.config is imported.
        print("\n.env file problem:\n")
        for item in error.errors():
            field = ".".join(str(part) for part in item["loc"]).upper()
            print(f"  {field}: {item['msg']}")
        print("\nOpen .env (next to run.py), fix the values above and start again.\n")
        sys.exit(1)

    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
