from datetime import datetime
import unittest

from bs4 import BeautifulSoup

from stuff.core import Stuff, Coordinates
from stuff.tests.utils import _data


class StuffTestCase(unittest.TestCase):
    def test_stuff_parse_item(self):
        list_item = BeautifulSoup(_data("zip_list_item.html"), features="html.parser")
        stuff = Stuff.parse_item(list_item, "newyork")
        expected = Stuff(
            url="https://newyork.craigslist.org/brk/zip/d/free-boxes-and-packing-supplies/6978063787.html",
            title="FREE BOXES and PACKING SUPPLIES",
            time=datetime(2019, 9, 13, 16, 31),
            price=0,
            neighborhood="Clinton Hill",
            city="newyork",
        )
        self.assertEqual(stuff, expected)

    def test_stuff_parse_details(self):
        stuff = Stuff(
            url="https://newyork.craigslist.org/brk/zip/d/free-boxes-and-packing-supplies/6978063787.html",
            title="FREE BOXES and PACKING SUPPLIES",
            time=datetime(2019, 9, 13, 16, 31),
            price=0,
            neighborhood="Clinton Hill",
            city="newyork",
        )
        item_page = BeautifulSoup(_data("craigslist_zip_item_page.html"), features="html.parser")
        stuff.parse_details(item_page)
        expected = Stuff(
            url="https://newyork.craigslist.org/brk/zip/d/free-boxes-and-packing-supplies/6978063787.html",
            title="FREE BOXES and PACKING SUPPLIES",
            time=datetime(2019, 9, 13, 16, 31),
            price=0,
            neighborhood="Clinton Hill",
            coordinates=Coordinates(longitude='-73.957000', latitude='40.646700'),
            image_urls=['https://images.craigslist.org/00L0L_5e2M7zY0JYR_600x450.jpg'],
            city="newyork",
        )
        self.assertEqual(stuff, expected)
