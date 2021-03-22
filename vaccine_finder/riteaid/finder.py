import os
import json
from pprint import pprint, pformat
import logging
import requests

from vaccine_finder.config import DEFAULT_INPUT_FILE
from vaccine_finder.utils import setup_logger, send_request
from vaccine_finder.notify import Notifier
from vaccine_finder.base import BaseAppointmentFinder

CHECK_SLOTS_ENDPOINT = (
    "https://www.riteaid.com/services/ext/v2/vaccine/checkSlots"
)
GET_STORES_ENDPOINT = "https://www.riteaid.com/services/ext/v2/stores/getStores"
SCHEDULER_ENDPOINT = "https://www.riteaid.com/pharmacy/apt-scheduler"
VACCINE_DOSE_IDS = ["1"]
STORE_LABEL = "RiteAid"


class RiteAidAppointmentFinder(BaseAppointmentFinder):
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

        Find RiteAids where there are available covid vaccine appointments
        """
        self.zip_codes = zip_codes or self.zip_codes
        self.radius = radius or self.radius

        self.logger.info("Starting vaccine finder ...")

        # Get list of stores to query
        stores = self._get_stores(self.zip_codes, self.radius)

        self.stores_with_appts = []
        for store in stores:
            store["fullAddress"] = (
                f'{store["address"]} {store["city"]}, {store["state"]} '
                f'{store["zipcode"]}'
            )
            self.logger.info(
                f"Checking RiteAid {store['storeNumber']} at "
                f"{store['fullAddress']}"
            )

            # Send request
            try:
                content = send_request(
                    self.session,
                    "get",
                    CHECK_SLOTS_ENDPOINT,
                    params={"storeNumber": store["storeNumber"]},
                )
            except requests.exceptions.RequestException as err:
                self.logger.error(
                    f"Error checking RiteAid {store['storeNumber']}: {err}"
                )

            self.logger.info(f"Received response:\n{pformat(content)}")

            # Check availability - for vaccine dose 1/2
            avail = self._check_availability(content, store)
            if avail:
                self.stores_with_appts.append(store)

        return len(self.stores_with_appts) > 0

    def _notification_message(self):
        """
        Create notification message to notify users (text, email)
        that appointments are available in stores
        """
        return "\n\n".join(
            [
                f"Store #{store['storeNumber']} at " f"{store['fullAddress']}"
                for store in self.stores_with_appts
            ]
        )

    def _check_availability(self, content, store):
        """
        Check if either vaccine dose 1 or 2 have open appointments
        """
        if self.debug:
            return True

        success = False
        for vaccine_dose in VACCINE_DOSE_IDS:
            if content["Data"]["slots"].get(vaccine_dose):
                success = True
                self.logger.info(
                    f"✅ Vaccine dose {vaccine_dose} available at RiteAid "
                    f"{store['storeNumber']} {store['fullAddress']}"
                )
            else:
                self.logger.info(
                    f"❌ Vaccine dose {vaccine_dose} not available at RiteAid "
                    f"{store['storeNumber']} {store['fullAddress']}"
                )
        return success

    def _get_stores(self, zip_codes, radius):
        """
        Get list of RiteAid stores in zip code within radius
        """
        stores = {}
        for zip_code in zip_codes:
            params = {
                "address": zip_code,
                "radius": radius,
                # Only get stores offering vaccines
                "attrFilter": "PREF-112",
                "fetchMechanismVersion": 2,
            }
            # Send request
            try:
                content = send_request(
                    self.session, "get", GET_STORES_ENDPOINT, params=params
                )
            except requests.exceptions.RequestException as err:
                self.logger.error(f"Error getting available stores: {err}")

            stores.update(
                {s["address"]: s for s in content["Data"]["stores"]}
            )
            self.logger.info(
                f"Found {len(stores)} stores in zip code {zip_code} within "
                f"radius {radius} miles"
            )
        return stores.values()


if __name__ == "__main__":
    f = RiteAidAppointmentFinder(debug=True)
    success = f.find(notify=False)
