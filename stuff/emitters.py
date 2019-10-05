import attr
from stuff.core import Stuff

from twitter import Api, Status
from twilio.rest import Client


@attr.s
class EmitStdout:
    def emit(self, stuff) -> str:
        print("New Stuff: {}".format(stuff.title))
        return "stdout: success"


@attr.s
class EmitSms:
    twilio_client: Client = attr.ib()
    from_phone: str = attr.ib()
    to_phone: str = attr.ib()

    @classmethod
    def new(cls, account_sid, auth_token, from_phone, to_phone):
        client = Client(account_sid, auth_token)
        return cls(client, from_phone, to_phone)

    def emit(self, stuff: Stuff):  # returns wtf that Message object is...
        message_body = "URGENT! ATTENTION! {} for {} at {}. Click {} for more details".format(
            stuff.title, stuff.price, stuff.neighborhood, stuff.url,
        )
        message = self.twilio_client.messages.create(
            body=message_body,
            from_=self.from_phone,
            to=self.to_phone,

        )
        # NOTE: wtf is the twilio api and where are the docs
        return message


@attr.s
class EmitTweet:
    twitter_api: Api = attr.ib()

    @classmethod
    def new(cls, consumer_key, consumer_secret, access_token_key, access_token_secret):
        api = Api(consumer_key, consumer_secret, access_token_key, access_token_secret)
        return cls(api)

    def emit(self, stuff: Stuff) -> Status:
        message_body = "{} for {} at {}. Click {} for more details".format(
            stuff.title, stuff.price, stuff.neighborhood, stuff.url,
        )
        status = self.twitter_api.PostUpdate(message_body)
        return status
