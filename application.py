import requests
from flask import Flask, redirect, render_template, request, jsonify
from cs50 import SQL
import os
import json
from datetime import datetime
import time
query = {}
# Key and token to authorize API request from "https://www.accounts.amadeus.com/LoginService/authorize?service=PAA&redirect_uri=https%3A%2F%2Fdevelopers.amadeus.com%2F&scope=openid&response_mode=fragment"
# username: hishamss90@gmail.com
# Pass: P@$$for$ure2669
API_KEY = "ETDSGTEkvLY9GCftMItd3qUGCV24HlCl"
API_SECRET = "3xvgDFZ8YGF7WaHT"
payload = dict()
payload['grant_type'] = 'client_credentials'
payload['client_id'] = API_KEY
payload['client_secret'] = API_SECRET
app = Flask(__name__)
# Reload templates when they are changed
app.config["TEMPLATES_AUTO_RELOAD"] = True
# set Flask max age value to 0 instead of 12 hours(to see the updates on CSS or JS)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
@app.after_request
def after_request(response):
    """Disable caching"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response
@app.route("/")
def index():
    return render_template ("index.html")
@app.route("/search")
def search():
    origin = request.args.get("from")
    destination = request.args.get("to")
    dates = request.args.get("daterangepicker")
    if " - " in dates:
        departure_date = dates.split(' - ')[0]
        departure_date = datetime.strptime(departure_date, '%m/%d/%Y').strftime('%Y-%m-%d')
        return_date = "&returnDate=" + datetime.strptime(dates.split(' - ')[1], '%m/%d/%Y').strftime('%Y-%m-%d')
    else:
        departure_date = datetime.strptime(dates, '%m/%d/%Y').strftime('%Y-%m-%d')
        return_date = ''
    adults = request.args.get("adults")
    if not request.args.get("children"):
        children = ''
    else:
        children = "&children=" + request.args.get("children")
    
    if not request.args.get("infants"):
        infants = ''
    else:
        infants = "&infants=" + request.args.get("infants")
    if  request.args.get("class") == "First Class":
        travelClass = "FIRST"
    elif  request.args.get("class") == "Premium Economy":
        travelClass = "PREMIUM_ECONOMY"
    else:
        travelClass = (request.args.get("class")).upper()
    if request.args.get("nonstop") == None:
        nonStop = "false"
    else:    
        nonStop = (request.args.get("nonstop")).lower()
    max = '20'
    response = requests.post("https://test.api.amadeus.com/v1/security/oauth2/token", data=payload)
    auth = response.json()
    token = auth["access_token"]
    header = dict()
    header['Authorization'] = 'Bearer' + ' ' + token
    url = ("https://test.api.amadeus.com/v2/shopping/flight-offers?originLocationCode=" 
            + origin + "&destinationLocationCode=" + destination + "&departureDate="
            + departure_date + return_date + "&adults=" + adults + children + infants +
            "&travelClass=" + travelClass + "&nonStop=" + nonStop + "&max=" + max)
    response = requests.get(url, headers=header)
    global query
    query = json.loads(response.text)
    if len(query['data']) == 0:
        return render_template("result.html", status=False)
    else:    
        data_main_list = []
        data_main_dic = {'offer': '', 'trip' : [], 'price': ''}
        data_list = []
        data_dic = {'total': '', 'segments' : [] }
        temp = []
        temp1 = []
        # iterate over the flight offers
        for offers in query['data']:
                # get the offer ID
            data_main_dic['offer'] = offers['id']
            # get the price for each offer
            data_main_dic['price'] = offers['price']['total'] + ' ' + offers['price']['currency']
            # iterate over the itineraries for each offer
            for itineraries in offers['itineraries']:
                data_dic['total'] = itineraries['duration'][2:].lower()
                for segments in itineraries['segments']:
                    temp.append(segments['duration'][2:].lower())
                    temp.append(segments['departure']['iataCode'])
                    temp.append(segments['arrival']['iataCode'])
                    temp.append(format_date(segments['departure']['at']))
                    temp.append(format_date(segments['arrival']['at']))
                    temp.append(dictionary('carriers', segments['carrierCode']))
                    temp.append(dictionary('aircraft', segments['aircraft']['code']))
                    temp1.append(temp.copy())
                    temp.clear()
                data_dic['segments'] = temp1.copy()
                temp1.clear()
                data_list.append(data_dic.copy())
            data_main_dic['trip'] = data_list.copy()
            data_list.clear()
            data_main_list.append(data_main_dic.copy())
        return render_template("result.html", data=data_main_list, status=True)
@app.route("/check", methods=["GET"])
def check():
    From = request.args.get("from")
    From = From + '%'
    db = SQL("sqlite:////var/www/html/database/airport.db")
    rows = db.execute(f"SELECT airport, code FROM airports WHERE code LIKE :From", From=From)
    return jsonify(rows)
@app.route("/auto_list", methods=["GET"])
def auto_list():
    From = request.args.get("from")
    From = '%' + From + '%'
    db = SQL("sqlite:////var/www/html/database/airport.db")
    rows = db.execute(f"SELECT airport, code FROM airports WHERE airport LIKE :From", From=From)
    return jsonify(rows)    
def format_date(data):
    Date = data.split('T')[0]
    Time = data.split('T')[1][:5]
    time_12hour = (datetime.strptime(Time, "%H:%M")).strftime( "%I:%M %p")
    return (Date + ' ' + time_12hour)
def dictionary(key, data):
    if key == 'carriers':
        return (query['dictionaries']['carriers'][data])
    elif key == 'aircraft':
        return (query['dictionaries']['aircraft'][data])
