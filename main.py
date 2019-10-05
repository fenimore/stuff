import sys
import configparser
import argparse

from stuff.constants import Area, Region, Category
from stuff.search import Search, Proximinity
from stuff.emitters import EmitSms
from stuff.client import StatefulClient


welcome_message = """
  /$$$$$$   /$$                /$$$$$$   /$$$$$$
 /$$__  $$ | $$               /$$__  $$ /$$__  $$
| $$  \__//$$$$$$   /$$   /$$| $$  \__/| $$  \__/
|  $$$$$$|_  $$_/  | $$  | $$| $$$$    | $$$$
 \____  $$ | $$    | $$  | $$| $$_/    | $$_/
 /$$  \ $$ | $$ /$$| $$  | $$| $$      | $$
|  $$$$$$/ |  $$$$/|  $$$$$$/| $$      | $$
 \______/   \___/   \______/ |__/      |__/
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--secrets", default=".secrets")
    parser.add_argument("--region", default="new_york_city")
    parser.add_argument("--area", default="brooklyn")
    parser.add_argument("--category", default="furniture")
    parser.add_argument("--query", default=None)
    parser.add_argument("--zip")
    parser.add_argument("--distance", type=int, default=2)
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.secrets)

    sleep_time = int(config["app"]["sleep"])
    log_level = config["app"]["log"]

    client = StatefulClient.new(
        db_path="sqlite:///stuff.db",
        search=Search(
            region=Region[args.region],
            area=Area[args.area],
            category=Category[args.category],
            query=args.query,
            proximinity=Proximinity(args.distance, args.zip) if args.zip else None,
        ),
        emitter=EmitSms.new(
            account_sid=config["twilio-test"]["account_sid"],
            auth_token=config["twilio-test"]["auth_token"],
            from_phone=config["twilio-test"]["from_phone"],
            to_phone=config["twilio-test"]["to_phone"],
        ),
        sleep_seconds=sleep_time,
        log_level=log_level,
    )

    client.refresh()
    client.setup()
    try:
        client.loop()
    except KeyboardInterrupt:
        client.logger.info("Interrupted the loop with keyboard")
        sys.exit(0)
