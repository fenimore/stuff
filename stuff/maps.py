"""Chart where free things are.

The StuffCharter class is a wrapper around the folium
openstreetmap python object, which in turn generates a
leaflet map.

Example usage:

    >>> from stuff_scraper import StuffScraper
    >>> from stuff_charter import StuffCharter
    >>> stuffs = StuffScraper('montreal', 5, precise=True).stuffs
    >>> treasure_map = StuffCharter(stuffs)
    call save_map(path) generate html map
    >>> treasure_map.save_test_map() # saves map in current dir
    BEWARNED, this map is likely inaccurate:
    Craigslist denizens care not for computer-precision
"""
from typing import List
import os, re
import tempfile

import attr
from geopy.geocoders import Nominatim
from bs4 import BeautifulSoup
import requests
import folium
from folium import CssLink


NO_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/No_image_3x4.svg/300px-No_image_3x4.svg.png"


@attr.s
class Charter:
    """Post folium map of freestuffs.

    After constructing Mappify map object, call
    create_map and pass in map_path in order to create
    the HTML map.

    Attributes:
        - treasure_map -- an OSM folium map object
        - stuffs -- list of free stuff
        - city -- the user's location (city)
        - zoom -- default map zoom

    Keyword arguments:
        - stuffs -- a list of stuff objects
        - address -- for an optional map marker of the user address.
        - do_create_map -- set to False to override modify attributes
                           before create_map.
        - is_testing -- use to test module from commandline
        - is_flask -- automatically create map for treasure-map
        - zoom -- the map default zoom level
    stuffs, address=None, zoom=13,
                 do_create_map=True,
                 is_testing=False, is_flask=False):
    """
    stuffs: List = attr.ib()
    city: str = attr.ib()
    address: str = attr.ib(default=None)
    zoom: int = attr.ib(default=13)
    radius: int = attr.ib(default=15)
    map = attr.ib(default=None)

    def create_map(self):
        """Create a folium Map object, treasure_map.

        treasure_map can be used to save an html leaflet map.

        Keyword arguments:
            - is_testing -- creates a map in webmap directory
            - is_flask -- creates a flask map
        """
        start_coordinates = self.find_city_center()
        map_osm = folium.Map([start_coordinates[0], start_coordinates[1]], zoom_start=self.zoom)
        for stuff in self.stuffs:
            image = stuff.image_urls[0] if stuff.image_urls else NO_IMAGE
            html = """
                    <link rel='stylesheet' type='text/css'
                    href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css'>
                    <img src='{}' height='auto' width='160px' />
                    <h3>{}</h3>
                    <h4>{}</h4>
                    <a href='{}' target='_blank'>View Posting in New Tab</a>
            """.format(image, stuff.title, stuff.neighborhood, stuff.url)
            lat = stuff.coordinates.latitude or start_coordinates[0]
            lon = stuff.coordinates.longitude or start_coordinates[1]
            popup = folium.Popup(
                html,
                max_width=3000
            )
            if not lon or not lat:
                geolocator = Nominatim(user_agent="TreasureMap/2")
                findit = geolocator.geocode(self.city) # Last resort
                lat = findit.latitude
                lon = findit.longitude

            folium.CircleMarker(
                [lat, lon],
                radius=self.radius,
                popup=popup,
                color="#428aae",
                fill_color="white",
                fill_opacity=0.2,
            ).add_to(map_osm)
            if self.radius > 4:
                self.radius -= .2

        self.map = map_osm
        self.add_address()

    def save_map(self, map_path=None, css_children={}):
        """Create html map in map_path.

        Keyword arguments:
            - map_path -- the path to create_map in
            - css_path -- the path to override css
                          (defaults to bootstrap via folium)
        """
        path = map_path or os.path.join(tempfile.mkdtemp(), "raw_map.html")
        folium_figure = self.map.get_root()
        for key, css in css_children.items():
            folium_figure.header._children[key] = CssLink(css)

        with open(path, "+w") as fid:
            root = self.map.get_root()
            html = root.render()
            fid.write(html)

        return path

    def find_city_center(self):
        """Return city center longitude latitude."""
        if re.match("montreal", self.city, re.I):
            coord = [45.5088, -73.5878]
        elif re.match("newyork", self.city, re.I):
            coord = [40.7127, -74.0058]
        elif re.match("toronto", self.city, re.I):
            coord = [43.7, -79.4000]
        elif re.match("washingtondc", self.city, re.I):
            coord = [38.9047, -77.0164]
        elif re.match("vancouver", self.city, re.I):
            coord = [49.2827, -123.1207]
        elif re.match("sanfrancisco", self.city, re.I):
            coord = [37.773972, -122.431297]
        else:
            try:
                geolocator = Nominatim(user_agent="TreasureMap/2")
                findit = geolocator.geocode(self.city) # Last resort
                lat = findit.latitude
                lon = findit.longitude
                coord = [lat, lon]
            except:
                coord = [0,0] # This is a bit silly, null island
        return coord

    def add_address(self):
        """Add address to folium map"""
        if self.address != None:
            geolocator = Nominatim(user_agent="TreasureMap/2")
            try:
                add_lat = geolocator.geocode(self.address).latitude
                add_lon = geolocator.geocode(self.address).longitude
            except:
                add_lat = 0
                add_lon = 0
            text = self.address + str(add_lat) + str(add_lon)
            folium.Marker(
                location=[add_lat, add_lon],
                popup=text,
                icon=folium.Icon(color='red',icon='home')
            ).add_to(self.map)

    def colorize(self, stuff):
        """Return a color according to regex search.

        1. Furniture pattern, red
        2. Electronics pattern, blue
        3. Miscellaneous pattern, black
        4. no match, white

        colorize will return  with the first pattern found in
        that order.
        """
        PATTERN_1 = "(wood|shelf|shelves|table|chair|scrap|desk|oak|pine|armoire|dresser)"
        PATTERN_2 = "(tv|screen|écran|speakers|wire|electronic|saw|headphones|arduino|print|television)" #search NOT match
        PATTERN_3 = "(book|games|cool|guide|box)"

        COLOR_1 = "#FF0000" #red
        COLOR_2 = "#3186cc" #blue
        COLOR_3 = "#000000" #black

        COLOR_DEFAULT = "white"
        if re.search(PATTERN_1, stuff, re.I):
            color = COLOR_1
        elif re.search(PATTERN_2, stuff, re.I):
            color = COLOR_2
        elif re.search(PATTERN_3, stuff, re.I):
            color = COLOR_3
        else:
            color = COLOR_DEFAULT
        return color
