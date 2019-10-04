import time
import configparser
import argparse
import attr
from stuff.core import Stuff, EmitFailure
from stuff.constants import Area, Region, Category
from stuff.search import Search, Proximinity
from stuff.db import DBClient, DBStuff
from stuff.emit_sms import EmitSms
from stuff.emit_twitter import EmitTweet


class EmitStdout:
    def emit(self, stuff) -> str:
        print(stuff.title)
        return "print success"


@attr.s
class StatefulClient:
    db_client: DBClient = attr.ib()
    search: Search = attr.ib()
    emitter = attr.ib()  # interface Emitter... TODO: zope
    sleep_seconds = attr.ib()

    @classmethod
    def new(cls, db_path="sqlite://", search=Search(), emitter=EmitStdout(), sleep_seconds=3000):
        """
        default sqlite db is in-memory
        default emitter is stdout
        default sleep time is 3,000 seconds
        """
        db = DBClient.new(db_path)
        return cls(db, search, emitter, sleep_seconds)

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

    def populate_db(self):
        for item in self.search.get_inventory():
            stuff = DBStuff.from_api_model(item)
            if not self.db_client.get_stuff_by_url(stuff.url):
                self.db_client.insert_stuff(stuff)

    def deliver(self, stuff: Stuff) -> str:
        try:
            result = self.emitter.emit(stuff)
            stuff.delivered = True
            self.db_client.update_stuff(stuff)
        except EmitFailure as e:
            result = "Failure {}".format(e)
        return result

    def loop(self):
        # TODO: send all undelivered?
        # configure that somehow?
        while True:  # TODO: interrupt ctrl-c?
            try:
                self.populate_db()
                all_stuff = self.db_client.get_all_undelivered_stuff()
                if len(all_stuff) > 0:
                    result = self.deliver(all_stuff[0])
                    print(result)  # TODO: add loggin
            except Exception:
                pass
            time.sleep(self.sleep_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--secrets", default=".secrets")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.secrets)

    sms_emitter = EmitSms.new(
        account_sid=config["twilio"]["account_sid"],
        auth_token=config["twilio"]["auth_token"],
        from_phone=config["twilio"]["from_phone"],
        to_phone=config["twilio"]["to_phone"],
    )
    tweet_emitter= EmitTweet.new(
        consumer_key=config["twitter"]["consumer_key"],
        consumer_secret=config["twitter"]["consumer_secret"],
        access_token_key=config["twitter"]["access_token_key"],
        access_token_secret=config["twitter"]["access_token_secret"],
    )
    print(tweet_emitter)

    client = StatefulClient.new("sqlite:///stuff.db")
    client.setup()
    client.query(
        region=Region.new_york_city,
        area=Area.brooklyn,
        category=Category.furniture,
        keyword=None,
        proximinity=Proximinity(3, "11238"),
    )
    client.populate_db()
    all_stuff = client.db_client.get_all_stuff()

    for idx, stuff in enumerate(all_stuff[0:10]):
        print(f"{idx}: {stuff.title}")
    print(f"Length: {len(all_stuff)}")
    print(len(all_stuff))
