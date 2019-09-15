# Stuff

A simple craigslist client in python. Example application in `main.py`


```
(stuff) behemoth:stuff (master*) $ python main.py --zip 11238 --distance 1

  /$$$$$$   /$$                /$$$$$$   /$$$$$$
 /$$__  $$ | $$               /$$__  $$ /$$__  $$
| $$  \__//$$$$$$   /$$   /$$| $$  \__/| $$  \__/
|  $$$$$$|_  $$_/  | $$  | $$| $$$$    | $$$$
 \____  $$ | $$    | $$  | $$| $$_/    | $$_/
 /$$  \ $$ | $$ /$$| $$  | $$| $$      | $$
|  $$$$$$/ |  $$$$/|  $$$$$$/| $$      | $$
 \______/   \___/   \______/ |__/      |__/


Inventory Count: 45
Region: new_york_city Area: anywhere Category: free
Zip Code: 11420 Search Distance: 1 miles

Most Recent Item:
Title: Small remote control drone with camera - FOR PARTS, DOES NOT FLY
Neighborhood: Prospect Heights
https://newyork.craigslist.org/brk/zip/d/brooklyn-small-remote-control-drone/6969929402.html



1: enrich listings
2: print listings
3: quit
Enter an option:

```

Run the tests

    pip install -e .
    pip install responses pytest-mypy
    pytest -mypy -s
