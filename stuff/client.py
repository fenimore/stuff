import time
import attr
import logging
from logging import Logger

from stuff.core import Stuff
from stuff.constants import Area, Region, Category
from stuff.search import Search, Proximinity
from stuff.db import DBClient
from stuff.emitters import Emitter, EmitStdout


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
        logger = logging.getLogger("stufflib")
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s %(name)s %(levelname)s: %(message)s',
            datefmt='%m/%d/%y %H:%M:%S',
        )

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
        # check if things not in db exits
        new_items = [
            item for item in inventory
            if not self.db_client.get_stuff_by_url(item.url)
        ]
        if enrich_inventory and new_items:
            self.logger.info(f"Enriching {len(new_items)} items")
            new_items = Search.enrich_inventory(new_items)

        for item in new_items:
            item.delivered = set_delivered
            self.db_client.insert_stuff(item)
            self.logger.info("Insert: {}".format(item.title))

    def deliver(self, stuff: Stuff) -> str:
        try:
            result = self.emitter.emit(stuff)
            stuff.delivered = True
            self.db_client.update_stuff(stuff)
            self.logger.info(self.emitter.log(result))
        except Exception as e:
            result = "Failure Delivering {}".format(e)
            self.logger.error(result)
        return result

    def loop(self, with_media=False):
        self.logger.info("Initial Populating of Database with all stuff marked delivered")
        self.populate_db(set_delivered=True, enrich_inventory=with_media)
        self.logger.info("Starting Loop")
        while True:
            try:
                all_stuff = self.db_client.get_all_undelivered_stuff()
                if len(all_stuff) > 0:
                    self.logger.info("Emitting: {}".format(all_stuff[0].title))
                    self.deliver(all_stuff[0])
                else:
                    self.logger.debug("Nothing to emit")
                self.populate_db(enrich_inventory=with_media)
            except Exception as e:
                self.logger.error("Exception in main loop {}".format(e))
            self.logger.debug("Sleeping {} seconds".format(self.sleep_seconds))
            time.sleep(self.sleep_seconds)
