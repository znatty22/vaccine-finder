from abc import ABC, abstractmethod
import os
import json
from pprint import pprint, pformat
import logging
import requests

from vaccine_finder.utils import setup_logger, send_request
from vaccine_finder.notify import Notifier

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
INPUT_FILE = os.path.abspath(os.path.join(ROOT_DIR, "inputs.json"))
DEFAULT_PHONE_NUM = "+14846206937"
DEFAULT_ZIP_CODES = [19403]
DEFAULT_RADIUS = 50


class BaseAppointmentFinder(ABC):
    def __init__(
        self,
        store_label,
        scheduler_endpoint,
        debug=False,
        input_file=None,
        cookie_dict=None,
    ):
        setup_logger()
        self.logger = logging.getLogger(type(self).__name__)
        self.store_label = store_label
        self.scheduler_endpoint = scheduler_endpoint
        self.debug = debug

        self.logger.info("Initializing {type(self).__name__} ...")
        self.logger.info(f"DEBUG: {self.debug}")

        # Create session with cookie
        self.session = requests.Session()
        if cookie_dict:
            self.session.cookies = (
                requests.cookies.cookiejar_from_dict(cookie_dict)
            )

        # Read inputs - zip_code, radius, subscribers to notify
        fn = os.environ.get("INPUT_FILE")
        if (not input_file) and fn:
            self.input_file = os.path.abspath(os.path.join(ROOT_DIR, fn))
        else:
            self.input_file = INPUT_FILE

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
