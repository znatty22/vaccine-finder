import os
import json
from pprint import pprint, pformat
import logging

import requests
from bs4 import BeautifulSoup

from vaccine_finder.utils import setup_logger, send_request
from vaccine_finder.notify import Notifier
from vaccine_finder.base import BaseAppointmentFinder

AVAIL_ENDPOINT = (
    "https://www.wegmans.com/covid-vaccine-registration/"
)
SCHEDULER_ENDPOINT = (
    "https://www.wegmans.com/covid-vaccine-registration/"
)
STORE_LABEL = "Wegmans"

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
INPUT_FILE = os.path.abspath(os.path.join(ROOT_DIR, "inputs.json"))
TOTAL_PAGE_ELEMENTS = 306


class WegmansAppointmentFinder(BaseAppointmentFinder):
    def __init__(
        self,
        debug=False,
        input_file=INPUT_FILE,
        cookie_dict=None,
    ):
        super().__init__(
            STORE_LABEL, SCHEDULER_ENDPOINT,
            debug=debug, input_file=input_file, cookie_dict=cookie_dict
        )

    def _find(self, zip_code=None, radius=None):
        """
        Entrypoint for find script

        Find Wegmans where there are available covid vaccine appointments
        """
        zip_code = zip_code or self.zip_code
        self.zip_code = zip_code

        self.logger.info("Starting vaccine finder ...")

        # Send request
        try:
            content = send_request(
                self.session,
                "get",
                AVAIL_ENDPOINT,
                headers={"User-Agent": "Vaccine-Finder"}
            )
        except requests.exceptions.RequestException as err:
            self.logger.error(
                f"Error checking {self.store_label}"
            )
            raise

        self.logger.info(f"Received response:\n{pformat(content)}")

        # Check availability
        avail = self._check_availability(content)

        return avail

    def _notification_message(self):
        """
        Create notification message to notify users (text, email)
        that appointments are available in stores
        """
        return "There MIGHT be appointments! Wegmans webpage finally changed!"

    def _check_availability(self, content):
        """
        Check if there are any available appointments
        """
        if self.debug:
            return True

        soup = BeautifulSoup(content, 'html.parser')
        success = len([t for t in soup.findAll()]) != TOTAL_PAGE_ELEMENTS

        if success:
            self.logger.info(
                f"✅ Vaccine appointments available at "
                f"{self.store_label}"
            )
        else:
            self.logger.info(
                f"❌ Vaccine appointments not available at "
                f"{self.store_label}"
            )
        return success


if __name__ == "__main__":
    f = WegmansAppointmentFinder(debug=False)
    success = f.find(notify=False)
