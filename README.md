# Stuff

[![CircleCI](https://circleci.com/gh/fenimore/stuff/tree/master.svg?style=svg)](https://circleci.com/gh/fenimore/stuff/tree/master)

```
  /$$$$$$   /$$                /$$$$$$   /$$$$$$
 /$$__  $$ | $$               /$$__  $$ /$$__  $$
| $$  \__//$$$$$$   /$$   /$$| $$  \__/| $$  \__/
|  $$$$$$|_  $$_/  | $$  | $$| $$$$    | $$$$
 \____  $$ | $$    | $$  | $$| $$_/    | $$_/
 /$$  \ $$ | $$ /$$| $$  | $$| $$      | $$
|  $$$$$$/ |  $$$$/|  $$$$$$/| $$      | $$
 \______/   \___/   \______/ |__/      |__/

```

A simple and stateful craigslist client in python for tracking a search term and emitting alerts.

Run the tests

    pip install -e .
    pip install  pytest-mypy sqlalchemy responses aresponses  # for async responses
    pytest -mypy -s -vv  # test type hints

The twilio emission tests are skipped in CI (must create necessary authorization tokens)

## Configuration

Copy the `.secrets_example` file and fill in with valid credentials to start using twitter or sms emitters.

## Running Client

The an example use of the `stuff` client can be run using the `main.py` module:


    python main.py --zip 11001


```
from stuff.constants import Area, Region, Category
from stuff.search import Search, Proximinity
from stuff.emitters import EmitSms
from stuff.client import StatefulClient


client = StatefulClient.new(
    db_path="sqlite:///stuff.db",  # default is in memory
    search=Search(
        region=Region.new_york_city,
        area=Area.brooklyn,
        category=Category.furniture,
        query="rug",
        proximinity=Proximinity(3, "11238"),
    ),
    emitter=EmitSms.new(
        account_sid=config["twilio"]["account_sid"],
        auth_token=config["twilio"]["auth_token"],
        from_phone=config["twilio"]["from_phone"],
        to_phone=config["twilio"]["to_phone"],
    ),
    sleep_seconds=1800,
    log_level="INFO",
)

client.setup()  # create db (can leave out if db is already created)
try:
    client.loop()
except KeyboardInterrupt:
    client.log.info("Interrupted the loop with keyboard")
    sys.exit(0)
```
