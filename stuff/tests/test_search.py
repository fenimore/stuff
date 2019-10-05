from datetime import datetime
import unittest
import responses
import re

import pytest

from stuff.core import Stuff, Coordinates
from stuff.search import Search, Proximinity
from stuff.constants import Area, Category
from stuff.tests.utils import _data


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