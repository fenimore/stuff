import sys
import time
import configparser
import argparse
import attr
import logging
from logging import Logger

from stuff.core import Stuff, EmitFailure
from stuff.constants import Area, Region, Category
from stuff.search import Search, Proximinity
from stuff.db import DBClient
from stuff.emitters import EmitSms, Emitter, EmitStdout


@attr.s
class StatefulClient:
    db_client: DBClient = attr.ib()
    search: Search = attr.ib()
    emitter: Emitter = attr.ib()
    sleep_seconds: int = attr.ib()
    log: Logger = attr.ib()

    @classmethod
    def new(cls, db_path="sqlite://", search=Search(), emitter=EmitStdout(), sleep_seconds=3000, log_level="INFO"):
        """
        default sqlite db is in-memory
        default emitter is stdout
        default sleep time is 3,000 seconds
        """
        logger = logging.getLogger("stufflog")
        logging.basicConfig(level=log_level)

        db = DBClient.new(db_path)
        return cls(db, search, emitter, sleep_seconds, logger)

    def query(self, region: Region, area: Area, category: Category, keyword: str, proximinity: Proximinity):
        self.search = Search(
            region=region, area=area, category=category,
            query=keyword, proximinity=proximinity,
        )

    def setup(self):
        self.db_client.create_db()

    def refresh(self):
        self.db_client.drop_db()
        self.db_client.create_db()

    def populate_db(self, set_delivered=False):
        """
        populate_db will set all the stuff objects to delivered
        so that when the loop begins, there is no "catch up"
        or waterfall of emissions.
        """
        for item in self.search.get_inventory():
            # TODO: replace is try catch exception?
            if not self.db_client.get_stuff_by_url(item.url):
                item.delivered = set_delivered
                self.db_client.insert_stuff(item)
                self.log.info("Added delivered: {} item: {}".format(item.delivered, item.title))

    def deliver(self, stuff: Stuff) -> str:
        try:
            result = self.emitter.emit(stuff)
            stuff.delivered = True
            self.db_client.update_stuff(stuff)
        except EmitFailure as e:
            result = "Failure Delivering {}".format(e)
            self.log.error(result)
        return result

    def loop(self):
        self.populate_db(set_delivered=True)
        self.log.info("Starting Loop")
        while True:
            try:
                self.populate_db()
                all_stuff = self.db_client.get_all_undelivered_stuff()
                if len(all_stuff) > 0:
                    self.log.info("Emitting: {}".format(all_stuff[0].title))
                    result = self.deliver(all_stuff[0])
                    self.log.info("Result: {}".format(result))
                else:
                    self.log.debug("Nothing to emit")
            except Exception:
                pass
            self.log.debug("Sleeping {} seconds".format(self.sleep_seconds))
            time.sleep(self.sleep_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--secrets", default=".secrets")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.secrets)

    emitter = EmitSms.new(
        account_sid=config["twilio-test"]["account_sid"],
        auth_token=config["twilio-test"]["auth_token"],
        from_phone=config["twilio-test"]["from_phone"],
        to_phone=config["twilio-test"]["to_phone"],
    )

    emitter = EmitStdout()
    sleep_time = int(config["app"]["sleep"])
    log_level = config["app"]["log"]
    client = StatefulClient.new(
        db_path="sqlite:///stuff.db",
        search=Search(
            region=Region.new_york_city,
            area=Area.brooklyn,
            category=Category.furniture,
            query="rug",
            proximinity=Proximinity(3, "11238"),
        ),
        emitter=emitter,
        sleep_seconds=sleep_time,
        log_level=log_level,
    )

    client.refresh()
    client.setup()
    try:
        client.loop()
    except KeyboardInterrupt:
        client.log.info("Interrupted the loop with keyboard")
        sys.exit(0)
