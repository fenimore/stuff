from datetime import datetime
import os
import unittest
from unittest import skip
from unittest.mock import patch
import configparser

from twitter import Api, Status

from stuff.emitters import EmitTweet, EmitSms

from stuff.core import Stuff


@skip("CI doesn't have the .secrets for twilio sandbox test credentials")
class EmitterTestCase(unittest.TestCase):
    def setUp(self):
        config_path = os.path.join(os.path.dirname(__file__), "../../.secrets")
        config = configparser.ConfigParser()
        config.read(config_path)
        self.sms_emitter = EmitSms.new(
            account_sid=config["twilio-test"]["account_sid"],
            auth_token=config["twilio-test"]["auth_token"],
            from_phone=config["twilio-test"]["from_phone"],
            to_phone=config["twilio-test"]["to_phone"],
        )
        self.tweet_emitter = EmitTweet.new(
            consumer_key=config["twitter"]["consumer_key"],
            consumer_secret=config["twitter"]["consumer_secret"],
            access_token_key=config["twitter"]["access_token_key"],
            access_token_secret=config["twitter"]["access_token_secret"],
        )
        self.stuff = Stuff(
            title="Furniture", url="https://somewhere.com/",
            time=datetime(2019, 4, 20), price=0,
            neighborhood="Clinton Hill",
            coordinates=None, image_urls=None,
        )

    def _patched_post_update(self, message, media=None, longitude=None, latitude=None):
        return Status(id=123, user="myscreenname", created_at=datetime(2019, 4, 20), text=message)

    @patch.object(Api, "PostUpdate", _patched_post_update)
    def test_emit_tweet_success(self):
        "Twitter doesn't provide a sandbox api, and so this little patch is how I'm testing the emission..."
        status = self.tweet_emitter.emit(self.stuff)

        self.assertEqual(status.user, "myscreenname")
        self.assertEqual(status.id, 123)
        self.assertEqual(status.text, "Furniture for 0 at Clinton Hill. Click https://somewhere.com/ for more details")

    def test_emit_sms_success(self):
        message = self.sms_emitter.emit(self.stuff)
        self.assertEqual(message.status, "queued")
        self.assertIsNone(message.error_code)
        self.assertIsNone(message.price)
