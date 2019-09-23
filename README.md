# Stuff

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

A simple craigslist client in python. Example applications in `examples` directory.

Run the tests

    pip install -e .
    pip install  pytest-mypy sqlalchemy responses aresponses  # for async responses
    pytest -mypy -s -v  # test type hints


## Stateful Client

use a sqlite DB to keep track of your stuff inventory
