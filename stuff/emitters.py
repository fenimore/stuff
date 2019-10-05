import abc
import attr
from stuff.core import Stuff

from twitter import Api, Status
from twilio.rest import Client


class EmitFailure(Exception):
    pass


class Emitter(abc.ABC):
    @abc.abstractmethod
    def emit(self, stuff: Stuff):
        pass

    @abc.abstractmethod
    def log(self, status) -> str:
        pass


@attr.s
class EmitStdout(Emitter):
    def emit(self, stuff) -> str:
        print("New Stuff: {}".format(stuff.title))
        return "stdout: success"

    def log(self, result: str) -> str:
        return result


@attr.s
class EmitSms(Emitter):
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
        # NOTE: wtf is the twilio python api and where are the docs
        return message

    def log(self, message) -> str:
        return "SMS<sid:{} error_code:{} price:{} status:{}>".format(
            message.sid, message.error_code, message.price or 0, message.status,
        )


@attr.s
class EmitTweet(Emitter):
    twitter_api: Api = attr.ib()

    @classmethod
    def new(cls, consumer_key, consumer_secret, access_token_key, access_token_secret):
        api = Api(consumer_key, consumer_secret, access_token_key, access_token_secret)
        return cls(api)

    def emit(self, stuff: Stuff) -> Status:
        message_body = "{} for {}$!!! at {}.\nClick {} for more details".format(
            stuff.title, stuff.price, stuff.neighborhood, stuff.url,
        )
        if len(message_body) - len(stuff.url) > 280:
            message_body = message_body[:280]

        status = self.twitter_api.PostUpdate(
            message_body,
            media=stuff.image_urls or None,
            longitude=stuff.coordinates.longitude if stuff.coordinates else None,
            latitude=stuff.coordinates.latitude if stuff.coordinates else None,
        )
        return status

    def log(self, status) -> str:
        return "Tweet<id:{} user:{}>".format(status.id, status.user.screen_name)
