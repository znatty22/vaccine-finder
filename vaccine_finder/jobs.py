
from vaccine_finder.riteaid.finder import RiteAidAppointmentFinder


def riteaid_job():
    f = RiteAidAppointmentFinder(debug=False)
    success = f.find(notify=False)
