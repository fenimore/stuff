import argparse

from stuff import Client, Category, Region, Area, Proximinity

ITEM_STR = "Title: {}\nNeighborhood: {}\n{}\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="https://{}.craigslist.org/search/")
    parser.add_argument("--region", default="new_york_city")
    parser.add_argument("--area", default="anywhere")
    parser.add_argument("--category", default="free")
    parser.add_argument("--query")
    parser.add_argument("--zip")
    parser.add_argument("--distance", default=2)
    parser.add_argument("--with-details", action="store_true")
    args = parser.parse_args()

    if args.zip:
        proximinity = Proximinity(search_distance=args.distance, postal=args.zip)
    client = Client(
        root=args.root,
        region=Region[args.region],
        area=Area[args.area],
        category=Category[args.category],
        proximinity=proximinity if args.zip else None,
    )
    inventory = client.get_inventory(with_details=args.with_details)

    print("""
  /$$$$$$   /$$                /$$$$$$   /$$$$$$
 /$$__  $$ | $$               /$$__  $$ /$$__  $$
| $$  \__//$$$$$$   /$$   /$$| $$  \__/| $$  \__/
|  $$$$$$|_  $$_/  | $$  | $$| $$$$    | $$$$
 \____  $$ | $$    | $$  | $$| $$_/    | $$_/
 /$$  \ $$ | $$ /$$| $$  | $$| $$      | $$
|  $$$$$$/ |  $$$$/|  $$$$$$/| $$      | $$
 \______/   \___/   \______/ |__/      |__/

""")
    print("Inventory Count: {}".format(len(inventory)))
    print("Region: {} Area: {} Category: {}".format(args.region, args.area, args.category))
    if args.zip:
        print("Zip Code: {} Search Distance: {} miles".format(args.zip, args.distance))
    print("\nMost Recent Item:")
    print(ITEM_STR.format(inventory[0].title, inventory[0].hood, inventory[0].url))

    print("\n")
    print("1: enrich listings")
    print("2: print listings")
    print("3: quit")
    while True:
        option = input("Enter an option: ")
        if option == "1":
            print("Enriching inventory of size {}...".format(len(inventory)))
            Client.enrich_inventory(inventory)
        elif option == "2":
            for item in inventory:
                print(ITEM_STR.format(item.title, item.hood, item.url))
        elif option == "3":
            break
        else:
            print("Invalid choice: {}".format(option))
