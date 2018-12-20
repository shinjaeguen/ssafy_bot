# -*- coding: utf-8 -*-
"""
Created on Thu Dec 20 09:18:14 2018

@author: Rejt77
"""

import json
import os
import re
import urllib.request

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template
from selenium import webdriver


app = Flask(__name__)

slack_token = "xoxb-505014660117-508925924486-sXgEAvEgNwmJ53y7b5I2XSjt"
slack_client_id = "505014660117.506920557441"
slack_client_secret = "39c3b78fb0c1cd145cdc1e064b06cb15"
slack_verification = "E76JuzeBiAGjJXi3ATjNcgru"
sc = SlackClient(slack_token)


def find_company(day, status):
    if(int(day) < 10):
        day = '0' + day
    driver = webdriver.Chrome("C:\chromedriver.exe")
    driver.get("https://jasoseol.com/recruit")
    html = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html,'html.parser')
    results = []
    company_status = []
    company_name = []
    
    for labels in soup.find_all("div", day = "201812" + str(day)):
        
        for each in labels.find_all("div", class_="calendar-label start"):
            company_status.append(each.get_text().strip())
            
        for each in labels.find_all("div", class_="calendar-label end"):
            company_status.append(each.get_text().strip())
            
        for companies in labels.find_all("div", class_="company-name"):
            company_name.append(companies.get_text().strip())

    company_status = company_status[0:int((len(company_status))/2)]
    company_name = company_name[0:int((len(company_name))/2)]


    for i in range(0, len(company_status)):
        if(company_status[i] == status):
            results.append(company_name[i])


    return results





def _crawl_portal_keywords(text):
    company_list = []

    input_source = text.split()[1:3]

    if(int(input_source[0]) > 31 or int(input_source[0]) < 1):
        return "날짜를 정확히 입력해 주세요\n"

    company_list = find_company(input_source[0],input_source[1])

    print(company_list)
    
    return u'\n'.join(company_list)

# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        keywords = _crawl_portal_keywords(text)
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=keywords
        )

        return make_response("App mention message has been sent", 200,)

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})

@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                            })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})
    
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})

@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"

if __name__ == '__main__':
    app.run('127.0.0.1', port=8080)
