#!/usr/bin/env python3

from bot import ActivityBot


def main() -> None:
    activity_bot = ActivityBot("./config.yaml")
    activity_bot.main()


if __name__ == "__main__":
    main()
