import os
import json
from pprint import pprint, pformat
import logging
import requests

from vaccine_finder.utils import setup_logger, send_request
from vaccine_finder.notify import Notifier

CHECK_SLOTS_ENDPOINT = (
    "https://www.riteaid.com/services/ext/v2/vaccine/checkSlots"
)
GET_STORES_ENDPOINT = "https://www.riteaid.com/services/ext/v2/stores/getStores"
SCHEDULER_ENDPOINT = "https://www.riteaid.com/pharmacy/apt-scheduler"
VACCINE_DOSE_IDS = ["1"]

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
INPUT_FILE = os.path.abspath(os.path.join(ROOT_DIR, "inputs.json"))


class RiteAidAppointmentFinder(object):
    def __init__(
        self,
        debug=False,
        input_file=INPUT_FILE,
        cookie=None,
    ):
        self.logger = setup_logger()
        self.debug = debug

        # Create session with cookie
        self.session = requests.Session()
        if cookie:
            self.session.cookies = requests.cookies.cookiejar_from_dict(cookie)

        # Read inputs - zip_code, radius, subscribers to notify
        self.zip_code = 19403
        self.radius = 50
        self.subscribers = []
        if os.path.exists(input_file):
            with open(input_file) as json_file:
                inputs = json.load(json_file)
                self.zip_code = inputs["location"]["zip_code"]
                self.radius = inputs["location"]["radius"]
                self.subscribers = [
                    (k, v) for k, v in inputs["subscribers"].items()
                ]
                if self.debug:
                    self.subscribers = self.subscribers[0:1]

        self.notifier = Notifier()

    def find(self, *args, **kwargs):
        """
        See _find
        """
        success = True
        try:
            success = self._find(*args, **kwargs)
        except Exception as e:
            success = False
            self.logger.error("Something went wrong in vaccine finder!")
            self.logger.exception(str(e))

        if success:
            self.logger.info("✅ At least one store has appointments!")
        else:
            self.logger.info("🚫 No stores have appointments!")

        return success

    def _find(self, zip_code=None, radius=None, notify=True):
        """
        Entrypoint for find script

        Find RiteAids where there are available covid vaccine appointments
        """
        success = False
        zip_code = zip_code or self.zip_code
        radius = radius or self.radius

        self.logger.info("Starting vaccine finder ...")

        # Get list of stores to query
        stores = self.get_stores(zip_code, radius)
        if self.debug:
            stores = stores[0:2]

        stores_with_appts = []
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
            success = self.check_availability(content, store)
            if success:
                stores_with_appts.append(store)

        # Notify people with stores that have appointments
        if stores_with_appts:
            self.notify(stores_with_appts, send_notifications=notify)

        return success

    def check_availability(self, content, store):
        """
        Check if either vaccine dose 1 or 2 have open appointments
        """
        if self.debug:
            return True

        success = False
        for vaccine_dose in VACCINE_DOSE_IDS:
            if content["Data"]["slots"].get(vaccine_dose):
                success = True
                store["fullAddress"] = address
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

    def notify(self, stores, send_notifications=False):
        """
        Notify users (text, email) that appointments are available in stores
        """
        self.logger.info("Notifying users of open appointments ...")
        messages = [
            "--------------------",
            "🚑 RiteAid Stores with Open Appointments!!!",
        ]
        for store in stores:
            messages.append(
                f"Store #{store['storeNumber']} at " f"{store['fullAddress']}"
            )
        messages.append(f"➡ To register, go to {SCHEDULER_ENDPOINT}")
        output = "\n\n".join(messages)
        if send_notifications:
            self.notifier.send_texts(
                output, phone_numbers=[ph for ph, email in self.subscribers]
            )
            self.logger.info(
                f"Sent texts to subscribers: {pformat(self.subscribers)}"
            )
        self.logger.info(output)

    def get_stores(self, zip_code, radius):
        """
        Get list of RiteAid stores in zip code within radius
        """
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
        stores = content["Data"]["stores"]
        self.logger.info(
            f"Found {len(stores)} stores in zip code {zip_code} within radius "
            f"{radius} miles"
        )
        return stores


if __name__ == "__main__":
    f = RiteAidAppointmentFinder(debug=False)
    success = f.find(notify=False)
