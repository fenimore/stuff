from typing import List, ValuesView, Optional
import attr
import os
from urllib.parse import urlencode

from bs4 import BeautifulSoup
import requests

from stuff.core import Stuff
from stuff.constants import Area, Region, Category

import asyncio
from aiohttp import ClientSession


@attr.s
class Proximinity:
    search_distance: int = attr.ib()
    postal: str = attr.ib()


@attr.s
class Search:
    """
    Search object is used to construct valid searches on craigslist
    and return inventory of `Stuff` listings from the search.
    """
    root: str = attr.ib(default="https://{}.craigslist.org/search/")
    region: Region = attr.ib(default=Region.new_york_city)
    area: Area = attr.ib(default=Area.anywhere)
    category: Category = attr.ib(default=Category.free)
    query: Optional[str] = attr.ib(default=None)
    proximinity: Optional[Proximinity] = attr.ib(default=None)
    # size: int = attr.ib(default=None)  # TODO: pagination size, if supporting pagination

    def build_url(self) -> str:
        base_url = os.path.join(
            self.root.format(self.region.value),
            self.area.value,
            self.category.value,
        )
        params = {}
        if self.query:
            params.update({"query": self.query})
        if self.proximinity:
            params.update({
                "search_distance": str(self.proximinity.search_distance),
                "postal": self.proximinity.postal,
            })
        if params:
            url_params = urlencode(params)
            return base_url + "?" + url_params
        else:
            return base_url

    def get_text(self) -> str:
        url = self.build_url()
        r = requests.get(url)
        return r.text

    def get_inventory(self) -> List[Stuff]:
        soup = BeautifulSoup(self.get_text(), features="html.parser")
        ul = soup.find("ul", {"class": "rows"})
        inventory = []
        for list_item in ul.find_all("li"):
            stuff = Stuff.parse_item(list_item)
            stuff.city = self.region
            inventory.append(stuff)
        return inventory

    def get_enriched_inventory(self, proxy=None) -> List[Stuff]:
        inventory = self.get_inventory()
        return self.enrich_inventory(inventory, proxy=proxy)

    @classmethod
    def enrich_inventory(cls, stuff: List[Stuff], proxy=None) -> List[Stuff]:
        """
        certain details of stuff are only accessible after visiting
        their unique URL (rather than simply scraping it from the listings page).

        the Coordinates and Image Urls are all "enriched"

        Because this function makes between 1 and 120 requests, it's executed
        asynchronously with asyncio.
        """
        return asyncio.run(cls._async_enrich_inventory(stuff, proxy))  # type: ignore

    @classmethod
    async def _async_details(cls, url, session, proxy=None):
        async with session.get(url, proxy=proxy) as response:
            return (await response.text(), url)

    @classmethod
    async def _async_enrich_inventory(cls, inventory: List[Stuff], proxy=None) -> ValuesView[Stuff]:
        tasks = []
        stuffs = {}
        async with ClientSession() as session:
            for item in inventory:
                task = asyncio.create_task(cls._async_details(item.url, session, proxy))
                tasks.append(task)
                stuffs[item.url] = item
            texts = await asyncio.gather(*tasks)
            for text, url in texts:
                stuffs[url].parse_details(BeautifulSoup(text, features="html.parser"))
            return stuffs.values()
