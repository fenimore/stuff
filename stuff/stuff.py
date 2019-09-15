from typing import List
from bs4.element import Tag
import attr
from datetime import datetime


@attr.s
class Coordinates:
    longitude: int = attr.ib()
    latitude: int = attr.ib()


def _strip_currency(price) -> int:
    return int(str(price).strip("$"))


@attr.s
class Stuff:
    """
    Stuff object is represents a Craigslist listing.
    """
    url: str = attr.ib()
    title: str = attr.ib()
    time: datetime = attr.ib()
    price: int = attr.ib(converter=_strip_currency)
    hood: str = attr.ib()  # TODO: strip parens conv
    image_urls: List[str] = attr.ib(default=None)
    coordinates: Coordinates = attr.ib(default=None)

    @classmethod
    def parse_item(cls, tag: Tag):
        """
        parse the <li> tag and return the Stuff
        """
        a_href = tag.find("a", href=True, text=True)
        url = a_href["href"]
        title = a_href.text
        time = datetime.strptime(tag.find("time")["datetime"], "%Y-%m-%d %H:%M")
        price = tag.find("span", {"class": "result-price"}).text.strip("$")
        hood_tag = tag.find("span", {"class": "result-hood"})
        hood = hood_tag.text.strip(" ()") if hood_tag else None
        return cls(url=url, title=title, time=time, price=price, hood=hood)

    def parse_details(self, page: Tag):
        """
        Populate the Stuff with with that item's individual page's information
        """
        img_tags = page.find_all("img", src=True)
        self.image_urls = [img["src"] for img in img_tags]
        map_div = page.find("div", {"id": "map"})
        if not map_div:
            return
        coord = Coordinates(
            longitude=map_div["data-longitude"],
            latitude=map_div["data-latitude"],
        )
        self.coordinates = coord
