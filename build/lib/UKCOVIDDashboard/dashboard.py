"""This is the main program of the covid data dashboard"""
import webbrowser
import json
import logging
from datetime import date
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
import covid_news_handling as cnh
import covid_data_handler as cdh

app = Flask(__name__)
logger = logging.getLogger("coviddashboard")

CONFIG = json.loads("".join(open("config.json","r").readlines()))
TODAY = date.strftime(date.today(), "%Y-%m-%d")

def initialise_logging():
    logging.getLogger("werkzeug").disabled = True
    log_format = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
    logger.setLevel(logging.DEBUG)
    
    fh = logging.FileHandler(CONFIG["logs_file_directory"]+TODAY+".log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(log_format)
    sh = logging.StreamHandler()
    sh.setLevel(logging.WARNING)
    sh.setFormatter(log_format)
    
    logger.addHandler(sh)
    logger.addHandler(fh)
    logger.info("Logging initialised, program is starting")

@app.route("/")
def main():
    return redirect("/index")

@app.route("/index")
def index():
    logger.info("Web Page Requested")
    cdh.S.run(blocking=False)
    if request.args.get("notif") != None:
        name = request.args.get("notif").replace("+"," ")
        cnh.delete_news_article(name)
    if request.args.get("update_item") != None:
        cdh.cancel_covid_updates(request.args.get("update_item"))
    if request.args.get("two") != None:
        kwargs = {"update_interval":cdh.time_to_delay(request.args.get("update")),
                  "update_name":request.args.get("two"),
                  "news":request.args.get("news") != None,
                  "data":request.args.get("covid-data") != None,
                  "repeat":request.args.get("repeat") != None
        }
        cdh.schedule_covid_updates(**kwargs)
    if len(request.args) > 0:
        return redirect(request.path)
    news = cnh.format_current_news()
    data = cdh.parse_json_data(CONFIG["covid_data_file"])
    update = cdh.format_updates()
    return render_template("index.html",    
                           title="COVID-19 Dashboard",
                           news_articles=news,
                           updates=update,
                           location=data["areaName"],
                           nation_location="England",
                           local_7day_infections=data["localInfections"],
                           national_7day_infections=data["nationalInfections"],
                           hospital_cases="Current Hospital Cases: " + str(data["hospitalCases"]),
                           deaths_total="Total Deaths: " + str(data["totalDeaths"])
                           )

if __name__ == "__main__":
    initialise_logging()
    try:
        webbrowser.open("http://127.0.0.1:5000", new=2)
        app.run()
    finally:
        logger.info("Program Closed\n----------------------------------------------------------\n")
