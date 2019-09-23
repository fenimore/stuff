from typing import List
import attr
import os
from urllib.parse import urlencode

from bs4 import BeautifulSoup
import requests

from stuff import Stuff
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
    query: str = attr.ib(default=None)
    proximinity: Proximinity = attr.ib(default=None)
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
        print(":SDFSDF")
        print(url)
        r = requests.get(url)
        return r.text

    def get_inventory(self) -> List[Stuff]:
        soup = BeautifulSoup(self.get_text(), features="html.parser")
        ul = soup.find("ul", {"class": "rows"})
        inventory = []
        for list_item in ul.find_all("li"):
            stuff = Stuff.parse_item(list_item)
            inventory.append(stuff)
        return inventory

    @classmethod
    def enrich_inventory(cls, stuff: List[Stuff]) -> List[Stuff]:
        return asyncio.run(cls._async_enrich_inventory(stuff))

    @classmethod
    async def async_details(cls, url, session):
        async with session.get(url) as response:
            return (await response.text(), url)

    @classmethod
    async def _async_enrich_inventory(cls, inventory: List[Stuff]) -> List[Stuff]:
        tasks = []
        stuffs = {}
        async with ClientSession() as session:
            for item in inventory:
                task = asyncio.create_task(cls.async_details(item.url, session))
                tasks.append(task)
                stuffs[item.url] = item
            texts = await asyncio.gather(*tasks)
            for text, url in texts:
                stuffs[url].parse_details(BeautifulSoup(text, features="html.parser"))
            return stuffs.values()
