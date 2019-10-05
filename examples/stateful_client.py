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
    """
    The StatefulClient is the main entrypoint for the `stuff` package.
    It ties together the necessary search and DB client
    with an arbitrary `stuff.emitters.Emitter`.

    client = StatefulClient.new()  # default Stdout emitter
    client.setup()  # create in memory db tables
    try:
        client.loop()
    except KeyboardInterrupt:
        client.log.info("Interrupted the loop with keyboard")
        sys.exit(0)
    """

    db_client: DBClient = attr.ib()
    search: Search = attr.ib()
    emitter: Emitter = attr.ib()
    sleep_seconds: int = attr.ib()
    logger: Logger = attr.ib()

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

    def populate_db(self, set_delivered=False, enrich_inventory=False):
        """
        populate_db will set all the stuff objects to delivered
        so that when the loop begins, there is no "catch up"
        or waterfall of emissions.

        the flag for enriching_inventory should be used if emitting
        using a media-ready emission API (not stdout or sms) like twitter
        """
        inventory = self.search.get_inventory()
        if enrich_inventory:
            inventory = Search.enrich_inventory(inventory)

        for item in inventory:
            if not self.db_client.get_stuff_by_url(item.url):
                item.delivered = set_delivered
                self.db_client.insert_stuff(item)
                self.logger.info("Added delivered: {} item: {}".format(item.delivered, item.title))

    def deliver(self, stuff: Stuff) -> str:
        try:
            result = self.emitter.emit(stuff)
            stuff.delivered = True
            self.db_client.update_stuff(stuff)
            self.logger.info(self.emitter.log(result))
        except EmitFailure as e:
            result = "Failure Delivering {}".format(e)
            self.logger.error(result)
        return result

    def loop(self):
        self.populate_db(set_delivered=True)
        self.logger.info("Starting Loop")
        while True:
            try:
                self.populate_db()
                all_stuff = self.db_client.get_all_undelivered_stuff()
                if len(all_stuff) > 0:
                    self.logger.info("Emitting: {}".format(all_stuff[0].title))
                    self.deliver(all_stuff[0])
                else:
                    self.logger.debug("Nothing to emit")
            except Exception:
                pass
            self.logger.debug("Sleeping {} seconds".format(self.sleep_seconds))
            time.sleep(self.sleep_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--secrets", default=".secrets")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.secrets)

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
        emitter=EmitSms.new(
            account_sid=config["twilio-test"]["account_sid"],
            auth_token=config["twilio-test"]["auth_token"],
            from_phone=config["twilio-test"]["from_phone"],
            to_phone=config["twilio-test"]["to_phone"],
        ),
        sleep_seconds=sleep_time,
        log_level=log_level,
    )

    client.refresh()  # delete old DB...
    client.setup()
    try:
        client.loop()
    except KeyboardInterrupt:
        client.log.info("Interrupted the loop with keyboard")
        sys.exit(0)
