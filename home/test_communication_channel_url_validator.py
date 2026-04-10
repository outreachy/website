from django.forms import ValidationError
from django.test import SimpleTestCase

from home.models import validate_irc_url


class CommunicationChannelUrlValidatorTests(SimpleTestCase):
    def assertValid(self, url):
        try:
            validate_irc_url(url)
        except ValidationError as e:
            self.fail(f"Expected valid URL, got ValidationError: {e}")

    def assertInvalid(self, url):
        with self.assertRaises(ValidationError):
            validate_irc_url(url)

    def test_valid_irc_urls_for_required_hosts(self):
        self.assertValid("irc://irc.gnome.org/#outreachy")
        self.assertValid("irc://irc.gnome.org/outreachy")
        self.assertValid("irc://irc.gimp.org/#gimp")
        self.assertValid("irc://irc.mozilla.org/#mozilla")
        self.assertValid("irc://irc.freenode.net/#channel")
        self.assertValid("irc://chat.freenode.net/#channel")

    def test_invalid_non_irc_scheme_for_required_hosts(self):
        self.assertInvalid("https://irc.gnome.org/#outreachy")
        self.assertInvalid("http://irc.mozilla.org/#mozilla")
        self.assertInvalid("https://irc.freenode.net/#channel")

    def test_reject_non_channel_irc_urls(self):
        self.assertInvalid("irc://irc.gnome.org")
        self.assertInvalid("irc://irc.gnome.org/")
        self.assertInvalid("irc://example.com")
        self.assertInvalid("irc://example.com/")

    def test_oftc_must_use_webchat_url(self):
        self.assertInvalid("irc://irc.oftc.net/#debian")
        self.assertInvalid("irc://irc.debian.org/#debian")
        self.assertInvalid("https://irc.oftc.net/#debian")

        self.assertValid("https://webchat.oftc.net/?channels=#debian")
        self.assertValid("https://webchat.oftc.net/?channels=%23debian")

        self.assertInvalid("http://webchat.oftc.net/?channels=#debian")
        self.assertInvalid("https://webchat.oftc.net/?channels=")

    def test_non_irc_urls_are_accepted_by_this_validator(self):
        # Non-IRC URLs are validated by URLValidator; this function should not reject them.
        self.assertValid("https://example.com/path")
        self.assertValid("http://lists.example.org/subscribe")

