import os
import logging
import datetime

from vaccine_finder.config import (
    DEFAULT_INPUT_FILE,
    WINDOW_START,
    WINDOW_END,
    NOTIFY_VACCINE_USERS,
    DEBUG_VACCINE_FINDER,
)
from vaccine_finder.riteaid.finder import RiteAidAppointmentFinder
from vaccine_finder.walgreens.finder import WalgreensAppointmentFinder
from vaccine_finder.wegmans.finder import WegmansAppointmentFinder
from vaccine_finder.allentown.finder import AllentownAppointmentFinder


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


def allentown_job():
    """
    Allentown Health Clinic Vaccine Finder Job during time window
    """
    f = AllentownAppointmentFinder(
        input_file=DEFAULT_INPUT_FILE,
        debug=DEBUG_VACCINE_FINDER
    )
    _finder_job(f)


def wegmans_job():
    """
    Wegmans Vaccine Finder Job during time window
    """
    f = WegmansAppointmentFinder(
        input_file=DEFAULT_INPUT_FILE,
        debug=DEBUG_VACCINE_FINDER
    )
    _finder_job(f)


def walgreens_job():
    """
    Walgreens Vaccine Finder Job during time window
    """
    f = WalgreensAppointmentFinder(
        input_file=DEFAULT_INPUT_FILE,
        debug=DEBUG_VACCINE_FINDER
    )
    _finder_job(f)


def riteaid_job():
    """
    Riteaid Vaccine Finder Job during time window
    """
    f = RiteAidAppointmentFinder(
        input_file=DEFAULT_INPUT_FILE,
        debug=DEBUG_VACCINE_FINDER
    )
    _finder_job(f)
