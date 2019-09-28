import argparse
import configparser
import twitter


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--secrets", default=".secrets")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.secrets)

    api = twitter.Api(
        consumer_key=config["twitter"]["consumer_key"],
        consumer_secret=config["twitter"]["consumer_secret"],
        access_token_key=config["twitter"]["access_token_key"],
        access_token_secret=config["twitter"]["access_token_secret"],
    )
    # status = api.PostUpdate("Hi Twitter!")
    status = api.GetFollowers()
    print(status)
