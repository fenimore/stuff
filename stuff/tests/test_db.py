import unittest
from datetime import datetime

from stuff.db import DBClient, DBStuff
from stuff.core import Stuff, Coordinates


class DBClientTestCase(unittest.TestCase):
    def setUp(self):
        self.client = DBClient.new("sqlite://")  # in memory
        self.client.drop_db()
        self.client.create_db()

    def test_client_insert_and_fetch_by_id(self):
        stuff_id = self.client.insert_stuff(
            Stuff(
                title="My Title", url="https://somewhere.com/",
                time=datetime(2019, 4, 20), price=0,
                neighborhood="Clinton Hill",
                coordinates=None, image_urls=None,
            )
        )
        actual = self.client.get_stuff_by_id(stuff_id)
        self.assertEqual(actual.title, "My Title")
        self.assertEqual(actual.id, stuff_id)
        self.assertEqual(actual.url, "https://somewhere.com/")

    def test_client_insert_and_fetch_by_url(self):
        stuff_id = self.client.insert_stuff(
            Stuff(
                title="My Title", url="https://somewhere.com",
                time=datetime(2019, 4, 20), price=0,
                neighborhood="Clinton Hill",
                coordinates=None, image_urls=None,
            )
        )
        actual = self.client.get_stuff_by_url("https://somewhere.com")
        self.assertEqual(actual.title, "My Title")
        self.assertEqual(actual.id, stuff_id)
        self.assertEqual(actual.url, "https://somewhere.com")

    def test_client_roundtrip_id(self):
        stuff_id = self.client.insert_stuff(
            Stuff(
                title="My Title", url="https://somewhere.com/",
                time=datetime(2019, 4, 20), price=0,
                neighborhood="Clinton Hill",
                coordinates=Coordinates(10.0, 10.0),
                image_urls=["https://somewhere.com/item/1", "https://somewhere.com/item/2"],
            )
        )
        api_model = self.client.get_stuff_by_id(stuff_id)
        self.assertEqual(api_model.id, stuff_id)
        db_stuff = DBStuff.from_api_model(api_model)
        self.assertEqual(db_stuff.id, stuff_id)
        roundtrip_stuff = db_stuff.to_api_model()
        # One of the urls are "lost here"
        self.assertEqual(roundtrip_stuff.image_urls, ['https://somewhere.com/item/1'])

    def test_client_update_stuff(self):
        stuff_id = self.client.insert_stuff(
            Stuff(
                title="My Title", url="https://somewhere.com/",
                time=datetime(2019, 4, 20), price=0,
                neighborhood="Clinton Hill",
                coordinates=None, image_urls=None,
            )
        )
        stuff = self.client.get_stuff_by_id(stuff_id)
        self.assertEqual(stuff.delivered, False)

        stuff.delivered = True
        self.client.update_stuff(stuff)

        updated_stuff = self.client.get_stuff_by_id(stuff.id)
        self.assertEqual(updated_stuff.delivered, True)
