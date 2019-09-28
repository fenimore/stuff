from datetime import datetime
import os
import unittest
import responses
import re

from bs4 import BeautifulSoup

import pytest

from stuff.core import Stuff, Coordinates
from stuff.db import DBClient, DBStuff
from stuff.search import Search, Proximinity
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
            neighborhood="Clinton Hill",
        )
        self.assertEqual(stuff, expected)

    def test_stuff_parse_details(self):
        stuff = Stuff(
            url="https://newyork.craigslist.org/brk/zip/d/free-boxes-and-packing-supplies/6978063787.html",
            title="FREE BOXES and PACKING SUPPLIES",
            time=datetime(2019, 9, 13, 16, 31),
            price=0,
            neighborhood="Clinton Hill",
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
        )
        self.assertEqual(stuff, expected)


class DBClientTestCase(unittest.TestCase):
    def setUp(self):
        self.client = DBClient.new("sqlite://")  # in memory
        self.client.drop_db()
        self.client.create_db()

    def test_client_insert_and_fetch_by_id(self):
        stuff_id = self.client.insert_stuff(
            DBStuff(
                title="My Title", url="https://somewhere.com/",
                time=datetime(2019, 4, 20), price=0,
                longitude=None, latitude=None, image_url=None,
            )
        )
        actual = self.client.get_stuff_by_id(stuff_id)
        self.assertEqual(actual.title, "My Title")
        self.assertEqual(actual.id, stuff_id)
        self.assertEqual(actual.url, "https://somewhere.com/")

    def test_client_insert_and_fetch_by_url(self):
        stuff_id = self.client.insert_stuff(
            DBStuff(
                title="My Title", url="https://somewhere.com",
                time=datetime(2019, 4, 20), price=0,
                longitude=None, latitude=None, image_url=None,
            )
        )
        actual = self.client.get_stuff_by_url("https://somewhere.com")
        self.assertEqual(actual.title, "My Title")
        self.assertEqual(actual.id, stuff_id)
        self.assertEqual(actual.url, "https://somewhere.com")

    def test_client_roundtrip_id(self):
        stuff_id = self.client.insert_stuff(
            DBStuff(
                title="My Title", url="https://somewhere.com/",
                time=datetime(2019, 4, 20), price=0,
                longitude=None, latitude=None, image_url=None,
            )
        )
        actual = self.client.get_stuff_by_id(stuff_id)
        self.assertEqual(actual.id, stuff_id)
        api_stuff = actual.to_api_model()
        self.assertEqual(api_stuff.id, stuff_id)
        roundtrip_stuff = DBStuff.from_api_model(api_stuff)
        self.assertEqual(roundtrip_stuff.id, stuff_id)

    def test_client_update_stuff(self):
        stuff_id = self.client.insert_stuff(
            DBStuff(
                title="My Title", url="https://somewhere.com/",
                time=datetime(2019, 4, 20), price=0,
                longitude=None, latitude=None, image_url=None,
            )
        )
        stuff = self.client.get_stuff_by_id(stuff_id)
        self.assertEqual(stuff.delivered, False)

        api_stuff = stuff.to_api_model()
        api_stuff.delivered = True
        update_stuff = DBStuff.from_api_model(api_stuff)
        self.client.update_stuff(update_stuff)

        updated_stuff = self.client.get_stuff_by_id(stuff.id)
        self.assertEqual(updated_stuff.delivered, True)


class SearchTestCase(unittest.TestCase):
    def test_search_build_url(self):
        c = Search()
        self.assertEqual(
            c.build_url(),
            'https://newyork.craigslist.org/search/zip',
            "Default should be free stuff in new york"
        )
        c = Search(area=Area.brooklyn, proximinity=Proximinity(1, "11238"))
        self.assertEqual(
            c.build_url(),
            'https://newyork.craigslist.org/search/brk/zip?search_distance=1&postal=11238',
        )

    def test_search_build_url_with_params(self):
        c = Search(category=Category.furniture, query="chairs and tables")
        self.assertEqual(
            c.build_url(),
            'https://newyork.craigslist.org/search/hsh?query=chairs+and+tables',
            "Parameters must be encoded"
        )
        c = Search(area=Area.brooklyn, proximinity=Proximinity(1, "11238"))
        self.assertEqual(
            c.build_url(),
            'https://newyork.craigslist.org/search/brk/zip?search_distance=1&postal=11238',
        )

    @responses.activate
    def test_search_get_text(self):
        search = Search()
        responses.add(responses.GET, search.build_url(), body=_data("craigslist_zip.html"))
        text = search.get_text()
        self.assertEqual("""\
<!DOCTYPE html>
<html class="no-js"><head>
    <title>new york free stuff  - craigslist</title>""", text[:95])
        self.assertEqual(289394, len(text))

    @responses.activate
    def test_search_get_inventory(self):
        search = Search()
        responses.add(responses.GET, search.build_url(), body=_data("craigslist_zip.html"))
        inventory = search.get_inventory()
        expected = Stuff(
            url='https://newyork.craigslist.org/brk/zip/d/brooklyn-2-round-blue-outdoor-side/6979177488.html',
            title='2 Round Blue Outdoor Side Tables',
            time=datetime(2019, 9, 15, 12, 15),
            price=0,
            neighborhood='Ditmas Park Area, Brooklyn',
            image_urls=None,
            coordinates=None,
        )
        self.assertEqual(expected, inventory[0])
        self.assertEqual(120, len(inventory))

        # responses.add(
        #     responses.GET,
        #     re.compile("https://newyork.craigslist.org/brk/zip/d/*"),
        #     body=_data("craigslist_zip_item_page_no_image.html"),
        # )

#        re.compile("\/[^]+\/zip\/d\/[^.]+\.html"),


@pytest.mark.asyncio
async def test_async_search_enrich_inventory(aresponses):
    inventory = [
        Stuff(url='https://newyork.craigslist.org/brk/zip/d/brooklyn-free-insulation/6977996917.html',
              title='FREE Insulation', time=datetime(2019, 9, 13, 15, 24), price=0,
              neighborhood='Bay Ridge, Brooklyn', image_urls=None, coordinates=None),
        Stuff(url='https://newyork.craigslist.org/brk/zip/d/brooklyn-large-navy-blue-area-rug-10-14/6977979965.html',
              title='Large navy blue area rug 10â\x80\x99 x 14â\x80\x99', time=datetime(2019, 9, 13, 14, 59),
              price=0, neighborhood='Greenpoint, Brooklyn', image_urls=None, coordinates=None),
        Stuff(url='https://newyork.craigslist.org/brk/zip/d/brooklyn-10-foot-round-pool/6977959276.html',
              title='10 foot round pool', time=datetime(2019, 9, 13, 14, 38), price=0, neighborhood='bklyn',
              image_urls=None, coordinates=None),
        Stuff(url='https://newyork.craigslist.org/brk/zip/d/brooklyn-microwave-popcorn-bags-free/6977920662.html',
              title='MICROWAVE POPCORN --- 8 BAGS --- FREE', time=datetime(2019, 9, 13, 13, 58), price=0,
              neighborhood='Bay Ridge', image_urls=None, coordinates=None),
    ]
    aresponses.add(
        "newyork.craigslist.org", re.compile(r"\/brk\/zip\/d\/brooklyn-free-insulation[^.]+\.html"),
        'get', aresponses.Response(text=_data("craigslist_zip_item_page.html"))
    )
    aresponses.add(
        "newyork.craigslist.org", re.compile(r"\/brk\/zip\/d\/brooklyn-large-navy[^.]+\.html"),
        'get', aresponses.Response(text=_data("craigslist_zip_item_page.html"))
    )
    aresponses.add(
        "newyork.craigslist.org", re.compile(r"\/brk\/zip\/d\/brooklyn-10-foot[^.]+\.html"),
        'get', aresponses.Response(text=_data("craigslist_zip_item_page.html"))
    )
    aresponses.add(
        "newyork.craigslist.org", re.compile(r"\/brk\/zip\/d\/brooklyn-microwave-popcorn[^.]+\.html"),
        'get', aresponses.Response(text=_data("craigslist_zip_item_page.html"))
    )
    expected = Stuff(
        url='https://newyork.craigslist.org/brk/zip/d/brooklyn-free-insulation/6977996917.html',
        title='FREE Insulation',
        time=datetime(2019, 9, 13, 15, 24),
        price=0,
        neighborhood='Bay Ridge, Brooklyn',
        image_urls=['https://images.craigslist.org/00L0L_5e2M7zY0JYR_600x450.jpg'],
        coordinates=Coordinates(longitude='-73.957000', latitude='40.646700')
    )
    assert expected != inventory[0]
    await Search._async_enrich_inventory(inventory)
    assert expected == inventory[0]
