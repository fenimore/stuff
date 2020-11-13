from functools import partial
from typing import List, Optional
import attr
import os
from multiprocessing.pool import ThreadPool
from urllib.parse import urlencode

from bs4 import BeautifulSoup
import requests

from stuff.core import Stuff
from stuff.constants import Area, Region, Category


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
            stuff = Stuff.parse_item(list_item, self.region.value)
            stuff.city = self.region.value
            inventory.append(stuff)
        return inventory

    @classmethod
    def enrich_item(cls, item: Stuff, proxies: Optional[dict]):
        text = requests.get(item.url, proxies=proxies).text
        item.parse_details(BeautifulSoup(text, features="html.parser"))
        return item

    @classmethod
    def enrich_inventory(
            cls,
            stuff: List[Stuff],
            proxies: Optional[dict] = None,
            num_threads: int = 4,
    ) -> List[Stuff]:
        """
        certain details of stuff are only accessible after visiting
        their unique URL (rather than simply scraping it from the listings page).

        the Coordinates and Image Urls are all "enriched"

        Because this function makes between 1 and 120 requests, it's executed
        asynchronously with asyncio.
        """
        with ThreadPool(num_threads) as p:
            map_enrich = partial(cls.enrich_item, proxies=proxies)
            return p.map(map_enrich, stuff)
