import os
from collections import defaultdict
from pprint import pprint, pformat
import json
import logging
import requests

CHECK_SLOTS_ENDPOINT = "https://www.riteaid.com/services/ext/v2/vaccine/checkSlots"
GET_STORES_ENDPOINT = "https://www.riteaid.com/services/ext/v2/stores/getStores"
COOKIE = ( 
    os.environ.get('RITEAID_COOKIE_NAME'),
    os.environ.get('RITEAID_COOKIE')
)
DEFAULT_ZIP_CODE = 19403
DEFAULT_RADIUS = 50
DEFAULT_STORES = {
    1733: "1400 West Main Street, Jeffersonville, PA 19403",
    11158: "160 North Gulph Road Ste1088, King Of Prussia, PA 19406",
}
CHECK_VACCINE_DOSES = ["1"]


class RiteAidAppointmentFinder(object):

    def __init__(
        self, zip_code=DEFAULT_ZIP_CODE, radius=DEFAULT_RADIUS,
        cookie=COOKIE
    ):
        self.logger = self.setup_logger()
        self.zip_code = zip_code
        self.radius = radius

        # Create session with cookie
        self.session = requests.Session()
        name, cookie = cookie
        if cookie:
            self.session.cookies = requests.cookies.cookiejar_from_dict(cookie)

    def setup_logger(self, log_level=logging.INFO):
        """
        Setup logger
        """
        format_ = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        root = logging.getLogger()
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logging.Formatter(format_))
        root.setLevel(log_level)
        root.addHandler(consoleHandler)
        logger = logging.getLogger(__name__)
        return logger

    def notify(self, stores):
        """
        Notify users (text, email) that appointments are available in stores
        """
        pass

    def get_stores(self, zip_code, radius):
        """
        Get list of RiteAid stores in zip code within radius
        """
        params = {
            "address": zip_code,
            "radius": radius,
            "attrFilter": "PREF-112",
            "fetchMechanismVersion": 2,
        }
        # Send request
        try:
            content = self.send_request(
                'get',
                GET_STORES_ENDPOINT,
                params=params
            )
        except requests.exceptions.RequestException as err:
            self.logger.error(
                f"Error getting available stores: {err}"
            )
        stores = content["Data"]["stores"]
        self.logger.info(
            f'Found {len(stores)} stores in zip code {zip_code} within radius '
            f'{radius} miles'
        )
        return stores

    def find(self, zip_code=DEFAULT_ZIP_CODE, radius=DEFAULT_RADIUS):
        """
        Entrypoint for find script

        Find RiteAids where there are available covid vaccine appointments
        """
        self.logger.info("Starting vaccine finder ...")

        # Get list of stores to query
        stores = self.get_stores(zip_code, radius) or DEFAULT_STORES

        stores_with_appts = defaultdict(list)
        for store in stores:
            store_number = store['storeNumber']
            address = (
                f'{store["address"]} {store["city"]}, {store["state"]} '
                f'{store["zipcode"]}'
            )
            self.logger.info(
                f"Checking RiteAid {store_number} at '{address}'"
            )

            # Send request
            try:
                content = self.send_request(
                    'get',
                    CHECK_SLOTS_ENDPOINT,
                    params={"storeNumber": store_number}
                )
            except requests.exceptions.RequestException as err:
                self.logger.error(
                    f"Error checking RiteAid {store_number}: {err}"
                )

            self.logger.info(f"Received response:\n{pformat(content)}")

            # Check availability - for vaccine dose 1/2
            for vaccine_dose in CHECK_VACCINE_DOSES:
                if content["Data"]["slots"].get(vaccine_dose):
                    stores_with_appts[store_number].append(vaccine_dose)
                    self.logger.info(
                        f"✅ Vaccine dose {vaccine_dose} available at RiteAid "
                        f"{store_number} {address}"
                    )
                else:
                    self.logger.info(
                        f"❌ Vaccine dose {vaccine_dose} not available at "
                        f"RiteAid {store_number} {address}"
                    )

        # Notify people with stores that have appointments
        if stores_with_appts:
            self.notify(stores_with_appts)

    def send_request(self, method_name, url, **kwargs):
        """
        Send HTTP request to url
        """
        http_method = getattr(self.session, method_name)
        response = http_method(url, **kwargs)
        response.raise_for_status()

        # Parse response
        try:
            content = response.json()
        except json.decoder.JSONDecodeError as e:
            self.logger.error(f'Got unexpected response:\n{response.text}')

        return content


if __name__ == "__main__":
    RiteAidAppointmentFinder().find()
