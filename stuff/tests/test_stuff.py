from datetime import datetime
import os
import unittest
import responses
import re

from bs4 import BeautifulSoup

from stuff.stuff import Stuff, Coordinates
from stuff.client import Client, Proximinity
from stuff.constants import Area, Category


def _data(filename: str) -> str:
    file_path = os.path.join(
        os.path.dirname(__file__), "data", filename
    )
    with open(file_path, "r") as file:
        return file.read()


class StuffTestCase(unittest.TestCase):
    def test_stuff_parse_item(self):
        list_item = BeautifulSoup(_data("zip_list_item.html"), features="html.parser")
        stuff = Stuff.parse_item(list_item)
        expected = Stuff(
            url="https://newyork.craigslist.org/brk/zip/d/free-boxes-and-packing-supplies/6978063787.html",
            title="FREE BOXES and PACKING SUPPLIES",
            time=datetime(2019, 9, 13, 16, 31),
            price=0,
            hood="Clinton Hill",
        )
        self.assertEqual(stuff, expected)

    def test_stuff_parse_details(self):
        stuff = Stuff(
            url="https://newyork.craigslist.org/brk/zip/d/free-boxes-and-packing-supplies/6978063787.html",
            title="FREE BOXES and PACKING SUPPLIES",
            time=datetime(2019, 9, 13, 16, 31),
            price=0,
            hood="Clinton Hill",
        )
        item_page = BeautifulSoup(_data("craigslist_zip_item_page.html"), features="html.parser")
        stuff.parse_details(item_page)
        expected = Stuff(
            url="https://newyork.craigslist.org/brk/zip/d/free-boxes-and-packing-supplies/6978063787.html",
            title="FREE BOXES and PACKING SUPPLIES",
            time=datetime(2019, 9, 13, 16, 31),
            price=0,
            hood="Clinton Hill",
            coordinates=Coordinates(longitude='-73.957000', latitude='40.646700'),
            image_urls=['https://images.craigslist.org/00L0L_5e2M7zY0JYR_600x450.jpg'],
        )
        self.assertEqual(stuff, expected)


class ClientTestCase(unittest.TestCase):
    def test_client_build_url(self):
        c = Client()
        self.assertEqual(
            c.build_url(),
            'https://newyork.craigslist.org/search/zip',
            "Default should be free stuff in new york"
        )
        c = Client(area=Area.brooklyn, proximinity=Proximinity(1, "11238"))
        self.assertEqual(
            c.build_url(),
            'https://newyork.craigslist.org/search/brk/zip?search_distance=1&postal=11238',
        )

    def test_client_build_url_with_params(self):
        c = Client(category=Category.furniture, query="chairs and tables")
        self.assertEqual(
            c.build_url(),
            'https://newyork.craigslist.org/search/hsh?query=chairs+and+tables',
            "Parameters must be encoded"
        )
        c = Client(area=Area.brooklyn, proximinity=Proximinity(1, "11238"))
        self.assertEqual(
            c.build_url(),
            'https://newyork.craigslist.org/search/brk/zip?search_distance=1&postal=11238',
        )

    @responses.activate
    def test_client_get_text(self):
        client = Client()
        responses.add(responses.GET, client.build_url(), body=_data("craigslist_zip.html"))
        text = client.get_text()
        self.assertEqual("""\
<!DOCTYPE html>
<html class="no-js"><head>
    <title>new york free stuff  - craigslist</title>""", text[:95])
        self.assertEqual(289394, len(text))

    @responses.activate
    def test_client_get_inventory_no_details(self):
        client = Client()
        responses.add(responses.GET, client.build_url(), body=_data("craigslist_zip.html"))
        inventory = client.get_inventory()
        expected = Stuff(
            url='https://newyork.craigslist.org/brk/zip/d/brooklyn-2-round-blue-outdoor-side/6979177488.html',
            title='2 Round Blue Outdoor Side Tables',
            time=datetime(2019, 9, 15, 12, 15),
            price=0,
            hood='Ditmas Park Area, Brooklyn',
            image_urls=None,
            coordinates=None,
        )
        self.assertEqual(expected, inventory[0])
        self.assertEqual(120, len(inventory))

    @responses.activate
    def test_client_get_inventory_with_details(self):
        client = Client()
        responses.add(responses.GET, client.build_url(), body=_data("craigslist_zip.html"))
        responses.add(
            responses.GET,
            re.compile("https://newyork.craigslist.org/brk/zip/d/*"),
            body=_data("craigslist_zip_item_page.html"),
        )
        inventory = client.get_inventory(with_details=True)
        expected = Stuff(
            url='https://newyork.craigslist.org/brk/zip/d/brooklyn-2-round-blue-outdoor-side/6979177488.html',
            title='2 Round Blue Outdoor Side Tables',
            time=datetime(2019, 9, 15, 12, 15),
            price=0,
            hood='Ditmas Park Area, Brooklyn',
            image_urls=['https://images.craigslist.org/00L0L_5e2M7zY0JYR_600x450.jpg'],
            coordinates=Coordinates(longitude='-73.957000', latitude='40.646700'),
        )
        self.assertEqual(expected, inventory[0])
        self.assertEqual(120, len(inventory))

    @responses.activate
    def test_client_get_inventory_with_details_no_image(self):
        client = Client()
        responses.add(responses.GET, client.build_url(), body=_data("craigslist_zip.html"))
        responses.add(
            responses.GET,
            re.compile("https://newyork.craigslist.org/brk/zip/d/*"),
            body=_data("craigslist_zip_item_page_no_image.html"),
        )
        inventory = client.get_inventory(with_details=True)
        expected = Stuff(
            url='https://newyork.craigslist.org/brk/zip/d/brooklyn-2-round-blue-outdoor-side/6979177488.html',
            title='2 Round Blue Outdoor Side Tables',
            time=datetime(2019, 9, 15, 12, 15),
            price=0,
            hood='Ditmas Park Area, Brooklyn',
            image_urls=[],
            coordinates=Coordinates(longitude='-73.544500', latitude='41.060200'),
        )
        self.assertEqual(expected, inventory[0])
        self.assertEqual(120, len(inventory))

    @responses.activate
    def test_client_enrich_inventory(self):
        client = Client()
        responses.add(responses.GET, client.build_url(), body=_data("craigslist_zip.html"))
        responses.add(
            responses.GET,
            re.compile("https://newyork.craigslist.org/brk/zip/d/*"),
            body=_data("craigslist_zip_item_page.html"),
        )
        inventory = client.get_inventory(with_details=False)
        self.assertEqual(120, len(inventory))
        expected = Stuff(
            url='https://newyork.craigslist.org/brk/zip/d/brooklyn-2-round-blue-outdoor-side/6979177488.html',
            title='2 Round Blue Outdoor Side Tables',
            time=datetime(2019, 9, 15, 12, 15),
            price=0,
            hood='Ditmas Park Area, Brooklyn',
            image_urls=['https://images.craigslist.org/00L0L_5e2M7zY0JYR_600x450.jpg'],
            coordinates=Coordinates(longitude='-73.957000', latitude='40.646700'),
        )
        self.assertNotEqual(expected, inventory[0])

        Client.enrich_inventory(inventory)
        self.assertEqual(expected, inventory[0])
