"""This module facilitates the data portion of the covid dashboard as well
as controls the scheduling and executing of data/news updates."""
import datetime
import json
import sched
import time
import logging
from uk_covid19 import Cov19API
import covid_news_handling as cnh

S = sched.scheduler(time.time, time.sleep)
CONFIG = json.loads("".join(open("config.json","r").readlines()))

logger = logging.getLogger("coviddashboard")

##################
###DATA SECTION###
##################
def parse_csv_data(filename) -> list:
    """Returns the contents of a CSV as a list of strings"""
    with open(filename) as file:
        return file.readlines()

def parse_json_data(filename) -> dict:
    """Returns the contents of a JSON file as a dict"""
    with open(filename, "r") as f:
        return json.loads("".join(f.readlines()))

def process_covid_csv_data(data) -> tuple:
    """Formats and processes CSV covid data.
    Returns the weekly cases, hospital cases and total deaths respectively"""
    for x in range(len(data)):
        data[x] = data[x].split(",")
    deaths_success, cases_success, = False, False
    last7days_count = 0
    last7days_cases = 0
    for row in data[1::]:
        if row[4] != '' and not deaths_success:
            total_deaths = int(row[4])
            deaths_success = True
        if row[5] != '' and not cases_success:
            current_hospital_cases = int(row[5])
            cases_success = True
        if row[6] != '' and last7days_count <= 8:
            if last7days_count > 1:
                last7days_cases += int(row[6])
            last7days_count += 1
        if (deaths_success and cases_success and last7days_count >= 7):
            break
    return (last7days_cases, current_hospital_cases, total_deaths)

def process_covid_API_data(data) -> dict:
    """Processes covid API data into a single dictionary"""
    final_data = {
        "areaName":None,
        "localInfections":0,
        "nationalInfections":0,
        "hospitalCases":None,
        "totalDeaths":None
    }
    local_count = 0
    national_count = 0
    for row in data:
        if row["areaName"] != None and final_data["areaName"] == None:
            final_data["areaName"] = row["areaName"]
        if row["hospitalCases"] != None and final_data["hospitalCases"] == None:
            final_data["hospitalCases"] = row["hospitalCases"]
        if row["totalDeaths"] != None and final_data["totalDeaths"] == None:
            final_data["totalDeaths"] = row["totalDeaths"]
        if row["localInfections"] != None and local_count < 7:
            final_data["localInfections"] += row["localInfections"]
            local_count += 1
        if row["nationalInfections"] != None and national_count < 7:
            final_data["nationalInfections"] += row["nationalInfections"]
            national_count += 1

        if (None not in final_data.values()) and local_count >= 7 and national_count >= 7:
            return final_data
    raise IndexError("Input was incomplete or too small to process")

def covid_API_request(location="Exeter",location_type="ltla",number_of_days=14) -> dict:
    """Retrieves and processes COVID data from the API"""
    logger.info("Data Requested")
    raw_data = request_raw_data(location,location_type)
    local_data = raw_data[0].get_json()["data"]
    national_data = raw_data[1].get_json()["data"]
    final_data = []
    for x in range(number_of_days):
        final_data.append(local_data[x])
        final_data[x].update(national_data[x])
    return process_covid_API_data(final_data)

def request_raw_data(location,location_type) -> tuple:
    """Returns raw COVID data for both local and national areas"""
    local_filters = ["areaType=" + location_type, "areaName=" + location]
    local_structure = {
    "areaName":"areaName",
    "date":"date",
    "localInfections":"newCasesByPublishDate",
    }
    national_filters = ["areaType=nation", "areaName=england"]
    national_structure = {
    "date":"date",
    "nationalInfections": "newCasesByPublishDate",
    "hospitalCases": "hospitalCases",
    "totalDeaths": "cumDeaths60DaysByDeathDate"
    }
    local_request = Cov19API(filters=local_filters,structure=local_structure)
    national_request = Cov19API(filters=national_filters,structure=national_structure)
    return (local_request, national_request)

def update_data_file(location="Exeter",location_type="ltla") -> None:
    """Retrieves and writes COVID data to a json file"""
    data = covid_API_request(location,location_type)
    data_json = json.dumps(data, indent=4)
    with open(CONFIG["covid_data_file"], "w") as f:
        f.writelines(data_json)

####################
###UPDATE SECTION###
####################
def schedule_covid_updates(update_interval, update_name, news=True, data=True, repeat=False) -> bool:
    """Schedules an update for covid data and/or news."""
    logger.info("Covid Update Scheduled: " + update_name)
    if not (news or data):
        news, data = True, True
    already_exists = False
    for update in S.queue:
        already_exists = update.kwargs["name"] == update_name or already_exists
    if not already_exists:
        update_args = {"name":update_name,
                       "news":news,
                       "data":data,
                       "repeat":repeat
                       }
        S.enter(update_interval, 1, run_covid_update, kwargs=update_args)
        S.run(blocking=False)
        return None
    logger.warning("Update scheduling failed! Did the update already exist?")
    return None

def cancel_covid_updates(name) -> None:
    """Cancels an update of name "name" if one is scheduled"""
    logger.info("Covid Update Cancelled: " + name)
    for event in S.queue:
        if event.kwargs["name"] == name:
            S.cancel(event)
            return None
    logger.warning("Failed to cancel update!")
    return None

def run_covid_update(name, news, data, repeat) -> None:
    """Updates covid data and/or news and schedules another update if """
    logger.info("Update " + name + " has been triggered")
    if news:
        cnh.update_news()
    if data:
        update_data_file(CONFIG["location"],CONFIG["location_type"])
    if repeat:
        schedule_covid_updates(86400, name, news, data, repeat)

def format_updates() -> list:
    """Formats all queued updates
    Returns a list of dictionaries containing the details of each update"""
    result = []
    today = datetime.datetime.timestamp((datetime.datetime.today()))
    for update in S.queue:
        title = update.kwargs["name"]
        interval = delay_to_datetime(update.time - today)
        content = "Scheduled for: " + interval + ".\n"
        if update.kwargs["news"]:
            content += "Refreshes News, "
        if update.kwargs["data"]:
            content  += "Refreshes Data, "
        if update.kwargs["repeat"]:
            content += "Repeats Daily, "
        result.append({"title":title,"content":content})
    return result

def delay_to_datetime(delay) -> str:
    """Returns a date and time string equal to the time from now after a delay in seconds"""
    today = datetime.datetime.today()
    seconds = today.timestamp() + delay
    dt = datetime.datetime.fromtimestamp(seconds)
    return dt.strftime("%Y-%m-%d %H:%M")

def time_to_delay(time_) -> float:
    """Returns a delay equal to the seconds from now until "time_"
    The format for "time_" is HH:MM"""
    today = datetime.datetime.today()
    conv_time = datetime.datetime.strptime(time_, "%H:%M").time()
    full_time = datetime.datetime.combine(today.date(),conv_time)
    if full_time < today:
        full_time += datetime.timedelta(days=1)
    result = datetime.datetime.timestamp(full_time) - datetime.datetime.timestamp(today)
    return result


if __name__ == "__main__":
    pass
