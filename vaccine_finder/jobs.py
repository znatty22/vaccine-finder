import os
import logging
import datetime

from vaccine_finder.riteaid.finder import RiteAidAppointmentFinder
from vaccine_finder.walgreens.finder import WalgreensAppointmentFinder

WINDOW_START = datetime.time(6, 0, 0, 0)  # 6 am
WINDOW_END = datetime.time(23, 59, 0, 0)  # ~ 12 am
NOTIFY_VACCINE_USERS = bool(int(os.environ.get("NOTIFY_VACCINE_USERS", False)))
DEBUG_VACCINE_FINDER = bool(int(os.environ.get("DEBUG_VACCINE_FINDER", False)))

logger = logging.getLogger('Jobs')


def in_range(t, start=WINDOW_START, end=WINDOW_END):
    """
    Check whether a time falls within a time window
    """
    if (t >= start) and (t <= end):
        return True
    return False


def _finder_job(finder):
    """
    Vaccine Finder Job during time window
    """
    t = datetime.datetime.now().time()
    logger.info(f"Time: {t}, Window: {WINDOW_START} to {WINDOW_END}")

    if in_range(datetime.datetime.now().time()):
        finder.find(notify=NOTIFY_VACCINE_USERS)
    else:
        logger.info(
            'Not time to run type(finder).__name__ finder. Sleeping ...'
        )


def walgreens_job():
    """
    Walgreens Vaccine Finder Job during time window
    """
    f = WalgreensAppointmentFinder(debug=DEBUG_VACCINE_FINDER)
    _finder_job(f)
#     f.find(notify=NOTIFY_VACCINE_USERS)


def riteaid_job():
    """
    Riteaid Vaccine Finder Job during time window
    """
    f = RiteAidAppointmentFinder(debug=DEBUG_VACCINE_FINDER)
    _finder_job(f)
#     f.find(notify=NOTIFY_VACCINE_USERS)
