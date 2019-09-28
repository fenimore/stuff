import attr
from stuff.constants import Area, Region, Category
from stuff.search import Search, Proximinity
from stuff.db import DBClient, DBStuff


@attr.s
class StatefulClient:
    db_client: DBClient = attr.ib()
    search: Search = attr.ib()

    @classmethod
    def new(cls, db_path="sqlite://", search=Search()):
        db = DBClient.new(db_path)
        return cls(db, search)

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


if __name__ == "__main__":
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
