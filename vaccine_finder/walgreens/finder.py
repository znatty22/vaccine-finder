import os
import datetime
import json
from pprint import pprint, pformat
import logging

import requests
from geopy.geocoders import Nominatim

from vaccine_finder.utils import setup_logger, send_request
from vaccine_finder.notify import Notifier
from vaccine_finder.base import BaseAppointmentFinder

AVAIL_ENDPOINT = (
    "https://www.walgreens.com/hcschedulersvc/svc/v1/immunizationLocations/availability"
)
SCHEDULER_ENDPOINT = (
    "https://www.walgreens.com/findcare/vaccination/covid-19/location-screening"
)
STORE_LABEL = "Walgreens"

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
INPUT_FILE = os.path.abspath(os.path.join(ROOT_DIR, "inputs.json"))


class WalgreensAppointmentFinder(BaseAppointmentFinder):
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
        self.geolocator = Nominatim(user_agent=type(self).__name__)

    def _find(self, zip_code=None, radius=None):
        """
        Entrypoint for find script

        Find Walgreens where there are available covid vaccine appointments
        """
        zip_code = zip_code or self.zip_code
        self.zip_code = zip_code

        self.logger.info("Starting vaccine finder ...")

        # Send request
        d = datetime.datetime.now().date().isoformat()
        loc = self.geolocator.geocode(str(zip_code))
        body = {
            "serviceId": "99",
            "position": {
                "latitude": loc.latitude,
                "longitude": loc.longitude
            },
            "appointmentAvailability": {"startDateTime": d},
            "radius": 25  # server complains if greater than 25
        }
        try:
            content = send_request(
                self.session,
                "post",
                AVAIL_ENDPOINT,
                json=body,
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
        return f"Stores in zip code {self.zip_code}"

    def _check_availability(self, content):
        """
        Check if there are any available appointments
        """
        if self.debug:
            return True

        success = content['appointmentsAvailable']
        if success:
            self.logger.info(
                f"✅ Vaccine appointments available at "
                f"{self.store_label} within zip code {self.zip_code}"
            )
        else:
            self.logger.info(
                f"❌ Vaccine appointments not available at "
                f"{self.store_label} within zip code {self.zip_code}"
            )
        return success


if __name__ == "__main__":
    f = WalgreensAppointmentFinder(debug=True)
    success = f.find(notify=True)
