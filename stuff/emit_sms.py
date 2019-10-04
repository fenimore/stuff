from typing import List, ValuesView, Optional
import attr
import os

from stuff.core import Stuff

from twilio.rest import Client


# import configparser
# config = configparser.ConfigParser()
# config.read(".secrets")
# account_sid = config["twilio"]["account_sid"]
# auth_token = config["twilio"]["auth_token"]
# phone_number = config["twilio"]["phone_number"]
# client = Client(account_sid, auth_token)

@attr.s
class EmitSms:
    twilio_client: Client = attr.ib()
    from_phone: str = attr.ib()
    to_phone: str = attr.ib()

    @classmethod
    def new(cls, account_sid, auth_token, from_phone, to_phone):
        client = Client(account_sid, auth_token)
        return cls(client, from_phone, to_phone)

    def emit(self, stuff: Stuff) -> str:
        message_body = "URGENT! ATTENTION! {} for {} at {}. Click {} for more details".format(
            stuff.title, stuff.price, stuff.neighborhood, stuff.url,
        )
        message = self.twilio_client.messages.create(
            body=message_body,
            from_=self.from_phone,
            to=self.to_phone,

        )
        # TODO: Wtf is the twilio api
        return message.sid
