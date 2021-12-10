"""This modules controls the retrieval, storage and formatting of news
articles from NewsAPI."""
import json
import logging
from datetime import date
from datetime import timedelta
import requests

CONFIG = json.loads("".join(open("config.json","r").readlines()))

logger = logging.getLogger("coviddashboard")

def news_API_request(covid_terms = "covid covid-19 coronavirus") -> dict:
    """Requests Covid-19 related news from the NewsAPI"""
    logger.info("News Requested")
    url = "https://newsapi.org/v2/everything?"
    keywords = " OR ".join(covid_terms.split())
    weeksdate = str(date.today()-timedelta(days=7))
    params = {
              "qInTitle":keywords,
              "from":weeksdate,
              "sortBy":"popularity",
              "apiKey":CONFIG["news_api_key"]}
    response = requests.get(url,params=params)
    return response.json()["articles"]

def update_news() -> None:
    """Adds news articles from an API request to the file of current news articles"""
    data = news_API_request()
    new_articles = 0
    json_dict = json.loads("".join(open(CONFIG["covid_news_file"], "r").readlines()))
    for article in data:
        item = {"title": article["title"],
                "source": article["source"]["name"],
                "url": article["url"]
                }
        if (item not in json_dict["current"]) and (item not in json_dict["deleted"]):
            json_dict["current"].insert(0, item)
            new_articles += 1
            if new_articles >= CONFIG["articles_per_refresh"]:
                break
    write_news_file(json_dict)

def delete_news_article(name) -> None:
    """Adds the first instance of an article 'name' to the deleted section"""
    logger.info("News article deleted")
    json_dict = json.loads("".join(open(CONFIG["covid_news_file"], "r").readlines()))
    for x in range(len(json_dict["current"])):
        article = json_dict["current"][x]
        if article["title"] == name:
            json_dict["deleted"].append(article)
            json_dict["current"].pop(x)
            break
    write_news_file(json_dict)

def write_news_file(data) -> None:
    """Overwrites the news json with the dictionary 'data'"""
    file = json.dumps(data, indent=4)
    with open(CONFIG["covid_news_file"], "w") as f:
        f.writelines(file)

def format_current_news() -> list:
    """Formats current news for use in main application"""
    result = []
    json_dict = json.loads("".join(open(CONFIG["covid_news_file"], "r").readlines()))
    for article in json_dict["current"]:
        title = article["title"]
        content = article["source"] + " - " + article["url"]
        result.append({"title":title,"content":content})
    return result

if __name__ == "__main__":
    pass
