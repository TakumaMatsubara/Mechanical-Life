from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from httplib2 import Http
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
)
import pydata_google_auth
import os
import urllib.request, json
import urllib.parse
import datetime
import requests
import pytz
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import openai


CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
CHATGPT_API_KEY = os.environ["CHATGPT_API_KEY"]


line_bot_api = LineBotApi(ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


@csrf_exempt
def callback(request):
    if request.method == "POST":
        signature = request.META["HTTP_X_LINE_SIGNATURE"]
        body = request.body.decode("utf-8")
        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()
        return HttpResponse("OK", status=200)


@handler.default()
def default(event):
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text="サポートされていないテキストメッセージです")
    )


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    # logger.info(event)
    user_id = event.source.user_id
    input_text = event.message.text
    if input_text.find("予定") >= 0 or input_text.find("スケジュール") >= 0:
        message, event_list = today_schedule(calendar_id="tamosongyuan3@gmail.com")
        weather = weather_forecast(event_list=event_list)
        message += weather
    elif input_text.find("食材") >= 0 or input_text.find("冷蔵庫") >= 0:
        message = food_suggest(user_id=user_id)
    else:
        message = free_talk(input_text=input_text)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


# def today_schedule(calendar_id: str)-> tuple:
def today_schedule(calendar_id: str) -> tuple:
    """今日のスケジュールを文字列とリストで取得する関数"""
    # 認証情報ファイルのパス
    credentials_json = os.environ["CREDENTIALS"]
    # GoogleカレンダーAPIのスコープ
    scopes = ["https://www.googleapis.com/auth/calendar.readonly"]

    # 認証情報を読み込む
    credentials_dict = json.loads(credentials_json)
    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict, scopes=scopes
    )

    # GoogleカレンダーAPIのクライアントを作成する
    service = build("calendar", "v3", credentials=credentials)

    # 今日の日付を取得する
    now = datetime.datetime.now(pytz.timezone("Asia/Tokyo"))
    start_of_day = datetime.datetime(
        now.year, now.month, now.day, tzinfo=pytz.timezone("Asia/Tokyo")
    )
    end_of_day = start_of_day + datetime.timedelta(days=1)

    # イベントの取得パラメータを設定する
    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    # イベントのリストを取得する
    events = events_result.get("items", [])

    # イベント情報を格納するリスト
    event_list = []

    schedule = ""
    if not events:
        schedule += "今日の予定はありません。"

    else:
        schedule += "今日の予定\n"
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
            summary = event["summary"]
            location = event.get("location", "")

            # 日付、時刻、イベントを分割してリストに格納
            start_datetime = datetime.datetime.fromisoformat(start)
            end_datetime = datetime.datetime.fromisoformat(end)
            date = start_datetime.date()
            start_hour = start_datetime.hour
            start_minute = start_datetime.minute
            end_hour = end_datetime.hour
            end_minute = end_datetime.minute

            event_info = {
                "date": date,
                "start_hour": start_hour,
                "start_minute": start_minute,
                "end_hour": end_hour,
                "end_minute": end_minute,
                "summary": summary,
                "location": location,
            }
            event_list.append(event_info)

            schedule += f"{start_hour}:{start_minute:02d}～{end_hour}:{end_minute:02d} {summary}\n"

    return (schedule, event_list)


def food_suggest(user_id: str) -> str:
    message = ""
    return message


def free_talk(input_text: str) -> str:
    openai.api_key = CHATGPT_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "関西弁で話して"},
            {"role": "system", "content": "発言の最後に「知らんけど。」をつけて"},
            {"role": "user", "content": f"{input_text}"},
        ],
    )

    message = response.choices[0]["message"]["content"].strip()
    return message


def weather_forecast(event_list: list) -> str:
    WEATHER_API_KEY = os.environ["WEATHER_API_KEY"]
    weather = None
    for event in event_list:
        if event["location"] == "":
            continue
        else:
            coordinate = get_coordinate(event=event)
            if coordinate != {}:
                url = f'http://api.openweathermap.org/data/2.5/forecast?lat={coordinate["latitude"]}&lon={coordinate["longitude"]}&appid={WEATHER_API_KEY}'
                response = requests.get(url)
                data = response.json()
                for forecast in data["list"]:
                    rain_probability = forecast["pop"]  # 降水確率

                    if rain_probability >= 50:
                        weather = f"{event['location']}で雨が降りそうやで！傘持っててな！"
                        break

        if weather != None:
            break
    if weather == None:
        weather = "今日は傘いらんで～"
    return weather


def get_coordinate(event: dict) -> dict:
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": event["location"], "key": GOOGLE_API_KEY}
    response = requests.get(url, params=params)
    data = json.loads(response.text)
    coordinate = {}
    if data["status"] == "OK":
        results = data["results"]
        for result in results:
            latitude = result["geometry"]["location"]["lat"]
            longitude = result["geometry"]["location"]["lng"]
            coordinate["latitude"] = latitude
            coordinate["longitude"] = longitude
    return coordinate


def index(request):
    return HttpResponse("This is bot api.")
