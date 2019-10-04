import attr
from stuff.core import Stuff
from twitter import Api


@attr.s
class EmitTweet:
    twitter_api: Api = attr.ib()

    @classmethod
    def new(cls, consumer_key, consumer_secret, access_token_key, access_token_secret):
        api = Api(consumer_key, consumer_secret, access_token_key, access_token_secret)
        return cls(api)

    def emit(self, stuff: Stuff) -> str:
        message_body = "{} for {} at {}. Click {} for more details".format(
            stuff.title, stuff.price, stuff.neighborhood, stuff.url,
        )
        status = self.twitter_api.PostUpdate(message_body)
        return status
