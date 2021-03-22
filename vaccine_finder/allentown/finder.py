import os
import json
from pprint import pprint, pformat
import logging

import requests
from bs4 import BeautifulSoup

from vaccine_finder.config import DEFAULT_INPUT_FILE
from vaccine_finder.utils import setup_logger, send_request
from vaccine_finder.notify import Notifier
from vaccine_finder.base import BaseAppointmentFinder

AVAIL_ENDPOINT = (
    "https://allentownpaclinics.schedulemeappointments.com/?mode=startreg&b2ZmZXJpbmdpZD00MjYx"
)
SCHEDULER_ENDPOINT = AVAIL_ENDPOINT
STORE_LABEL = "Allentown Health Clinic"


class AllentownAppointmentFinder(BaseAppointmentFinder):
    def __init__(
        self,
        debug=False,
        input_file=DEFAULT_INPUT_FILE,
        cookie_dict=None,
    ):
        super().__init__(
            STORE_LABEL, SCHEDULER_ENDPOINT,
            debug=debug, input_file=input_file, cookie_dict=cookie_dict
        )

    def _find(self, zip_codes=None, radius=None):
        """
        Entrypoint for find script

        Find Allentown where there are available covid vaccine appointments
        """
        self.zip_codes = zip_codes or self.zip_codes

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

        self.logger.debug(f"Received response:\n{pformat(content)}")

        # Check availability
        avail = self._check_availability(content)

        return avail

    def _notification_message(self):
        """
        Create notification message to notify users (text, email)
        that appointments are available in stores
        """
        return f"{STORE_LABEL} web page changed!!!"

    def _check_availability(self, content):
        """
        Check if there are any available appointments
        """
        if self.debug:
            return True

        success = "There are no openings available" not in content

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
    f = AllentownAppointmentFinder(debug=True)
    success = f.find(notify=True)
