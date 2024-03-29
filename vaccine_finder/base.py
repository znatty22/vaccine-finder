from abc import ABC, abstractmethod
import os
import json
from pprint import pprint, pformat
import logging
import requests

from vaccine_finder.config import (
    DEFAULT_INPUT_FILE,
    DEFAULT_PHONE_NUM,
    DEFAULT_ZIP_CODES,
    DEFAULT_RADIUS,
)
from vaccine_finder.utils import setup_logger, send_request
from vaccine_finder.notify import Notifier


class BaseAppointmentFinder(ABC):
    def __init__(
        self,
        store_label,
        scheduler_endpoint,
        debug=False,
        input_file=DEFAULT_INPUT_FILE,
        cookie_dict=None,
    ):
        setup_logger()
        self.logger = logging.getLogger(type(self).__name__)
        self.store_label = store_label
        self.scheduler_endpoint = scheduler_endpoint
        self.debug = debug
        self.input_file = input_file

        self.logger.info(f"Initializing {type(self).__name__} ...")
        self.logger.info(f"DEBUG: {self.debug}")
        self.logger.info(f"INPUTS: {self.input_file}")

        # Create session with cookie
        self.session = requests.Session()
        if cookie_dict:
            self.session.cookies = (
                requests.cookies.cookiejar_from_dict(cookie_dict)
            )

        # Read inputs - zip_code, radius, subscribers to notify
        self.zip_codes = DEFAULT_ZIP_CODES
        self.radius = DEFAULT_RADIUS
        self.subscribers = dict()
        if os.path.exists(self.input_file):
            with open(self.input_file) as json_file:
                inputs = json.load(json_file)
                self.zip_codes = inputs["location"]["zip_codes"]
                self.radius = inputs["location"]["radius"]
                self.subscribers = inputs["subscribers"]
                if self.debug:
                    self.subscribers = {
                        DEFAULT_PHONE_NUM: self.subscribers.get(
                            DEFAULT_PHONE_NUM
                        )
                    }
        else:
            self.logger.warning(
                f"⚠️  Input file {self.input_file} not found"
            )

        self.notifier = Notifier()

    def find(self, *args, **kwargs):
        """
        See _find
        """
        success = True
        try:
            notify = kwargs.pop('notify', False)
            self.logger.info(f"NOTIFY: {notify}")
            success = self._find(*args, **kwargs)
            if success:
                self.notify(send_notifications=notify)

        except Exception as e:
            success = False
            self.logger.error("Something went wrong in vaccine finder!")
            self.logger.exception(str(e))

        if success:
            self.logger.info("✅ At least one store has appointments!")
        else:
            self.logger.info("🚫 No stores have appointments!")

        return success

    def notify(self, send_notifications=False):
        """
        Notify users (text, email) that appointments are available in stores
        """
        self.logger.info("Notifying users of open appointments ...")
        messages = [
            "--------------------",
            f"🚑 {self.store_label} Stores Have Open Appointments!!!",
        ]
        custom_message = self._notification_message()
        messages.append(custom_message)
        messages.append(f"➡ To register, go to {self.scheduler_endpoint}")
        output = "\n\n".join(messages)
        if send_notifications:
            self.notifier.send_texts(
                output, phone_numbers=[
                    ph for ph, email in self.subscribers.items()
                ]
            )
            self.logger.info(
                f"Sent texts to subscribers: {pformat(self.subscribers)}"
            )
        self.logger.info(output)

    @abstractmethod
    def _find(self, *args, **kwargs):
        """
        Called by find method. Must return boolean indicating success or 
        not 

        MUST BE IMPLEMENTED BY SUBCLASSES
        """
        raise NotImplementedError

    @abstractmethod
    def _notification_message(self):
        """
        Return the message to put in the success notification sent to users

        MUST BE IMPLEMENTED BY SUBCLASSES
        """
        raise NotImplementedError
