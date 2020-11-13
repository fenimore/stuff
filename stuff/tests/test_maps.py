from datetime import datetime
import unittest

from bs4 import BeautifulSoup

from stuff.core import Stuff, Coordinates
from stuff.maps import Charter


class StuffCharterTestCase(unittest.TestCase):
    def setUp(self):
        self.stuffs = [
            Stuff(
                url="https://newyork.craigslist.org/brk/zip/d/free-couch/1234556.html",
                title="free couch",
                time=datetime(2019, 9, 13, 13, 31),
                price=0,
                neighborhood="Clinton Hill",
                city="newyork",
                coordinates=Coordinates(longitude='-73.947000', latitude='40.546700'),
                image_urls=['https://images.craigslist.org/someother.jpg']
            ),
            Stuff(
                url="https://newyork.craigslist.org/brk/zip/d/free-boxes-and-packing-supplies/6978063787.html",
                title="FREE BOXES and PACKING SUPPLIES",
                time=datetime(2019, 9, 13, 16, 31),
                price=0,
                city="newyork",
                neighborhood="Clinton Hill",
                coordinates=Coordinates(longitude='-73.957000', latitude='40.646700'),
                image_urls=['https://images.craigslist.org/00L0L_5e2M7zY0JYR_600x450.jpg']
            )
        ]
    def test_stuff_charter(self):

        charter = Charter(
            stuffs=self.stuffs,
            city="newyork",
        )
        charter.create_map()

        self.assertEqual(len(charter.map.to_dict()["children"]), 3)
        self.assertEqual(charter.map.to_dict()["name"], "Map")

    @unittest.skip("This test has no fake/mocked parts, don't run wiley niley")
    def test_stuff_charter_address(self):
        charter = Charter(
            stuffs=self.stuffs,
            city="newyork",
            address="420 Clinton Ave"
        )
        charter.create_map()

        self.assertEqual(len(charter.map.to_dict()["children"]), 4)
        self.assertEqual(charter.map.to_dict()["name"], "Map")

    def test_stuff_charter_save_map(self):

        charter = Charter(
            stuffs=self.stuffs,
            city="newyork",
        )
        charter.create_map()
        map_path = charter.save_map()

        with open(map_path, "r") as fid:
            self.assertEqual(fid.read()[0:15], "<!DOCTYPE html>")

        self.assertEqual(len(charter.map.to_dict()["children"]), 3)
        self.assertEqual(charter.map.to_dict()["name"], "Map")
