import os
import logging
from pprint import pprint, pformat

from twilio.rest import Client
from vaccine_finder.utils import setup_logger

DEFAULT_MESSAGE = "Hello world!"


class Notifier(object):

    def __init__(self, init_logger=False):
        account_sid = os.environ['TWILIO_ACCOUNT_ID']
        auth_token = os.environ['TWILIO_AUTH_TOKEN']
        if init_logger:
            setup_logger()
        self.logger = logging.getLogger(type(self).__name__)
        self.twilio_number = os.environ['TWILIO_PHONE_NUMBER']
        self.client = Client(account_sid, auth_token)

    def send_texts(self, message, phone_numbers):
        """
        Send text to list of phone numbers
        """
        for phone_number in phone_numbers:
            self.logger.info(f'📲 Sending text to {phone_number}')
            response = self.client.messages.create(
                body=message,
                from_=self.twilio_number,
                to=phone_number,
            )

    def send_emails(self, message, email_addresses):
        """
        Send emails to list of email addresses
        """
        pass


if __name__ == '__main__':
    Notifier().send_texts("Hi guys its nashu!!!!")
