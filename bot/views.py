from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from httplib2 import Http
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    ImageMessage
)
import pydata_google_auth
import os, io
import urllib.request, json
import urllib.parse
import datetime
import requests
import pytz
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import openai
from .models import User
import tempfile
from google.cloud import vision
import cv2



CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
CHATGPT_API_KEY = os.environ["CHATGPT_API_KEY"]
GOOGLE_REDIRECT_URI = os.environ["GOOGLE_REDIRECT_URI"]
CREDENTIALS = os.environ["CREDENTIALS"]
VOCAB_TXT = os.environ["VOCAB_TXT"]
USER_ID = os.environ["USER_ID"]

line_bot_api = LineBotApi(ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


def google_auth(request):
    credentials_dict = {
        "web": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uris": [GOOGLE_REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://accounts.google.com/o/oauth2/token"
        }
    }

    # 一時ファイルに認証情報を書き込む
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write(json.dumps(credentials_dict))

    # 一時ファイルのパスを取得
    temp_file_path = temp_file.name

    # Flow.from_client_secrets_file()メソッドで一時ファイルを使用
    flow = Flow.from_client_secrets_file(
        temp_file_path,
        scopes=['https://www.googleapis.com/auth/calendar.events.readonly'],
        redirect_uri=GOOGLE_REDIRECT_URI
    )

    # 一時ファイルを削除
    os.remove(temp_file_path)

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    request.session['state'] = state
    return redirect(authorization_url)


def google_auth_callback(request):
    state = request.session.pop('state', None)

    flow = Flow.from_client_secrets_file(
        'path/to/your/credentials.json',
        scopes=['https://www.googleapis.com/auth/calendar.events.readonly'],
        state=state,
        redirect_uri=GOOGLE_REDIRECT_URI
    )

    flow.fetch_token(authorization_response=request.get_full_path())

    credentials = flow.credentials

    # credentialsを使用してGoogleカレンダーAPIにアクセス

    return redirect("")  # 認証後にリダイレクトするURLを指定

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
    user_id = event.source.user_id
    print(user_id)
    input_text = event.message.text
    if input_text.find("予定") >= 0 or input_text.find("スケジュール") >= 0:
        message, event_list = today_schedule(calendar_id="tamosongyuan3@gmail.com")
        weather = weather_forecast(event_list=event_list)
        message += "\n＝以下天気予報＝\n"
        message += weather
    elif input_text.find("リマインド") >= 0:
        message = 'そろそろ移動したほうがええんちゃう\n移動に1時間44分かかるで～'
    else:
        message = free_talk(input_text=input_text)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    user_id = event.source.user_id
    print("user_id", user_id)
    # 画像を一時ファイルとして保存
    with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_image:
        message_content = line_bot_api.get_message_content(event.message.id)
        print("message_content", message_content)
        for chunk in message_content.iter_content():
            temp_image.write(chunk)
        temp_image.flush()
        print("temp_image", temp_image)

        # 画像から食材を認識
        vege_list = get_food_ingredients(temp_image.name)
        message = food_suggest(vege_list=vege_list)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))

def send_message_at_specific_time():
    now = datetime.datetime.now().time()
    target_time = datetime.time(hour=10, minute=42, second=0)  # 送信したい時刻を設定

    if now.hour == target_time.hour and now.minute == target_time.minute:
        user_id = USER_ID  # 送信先のユーザーIDを設定
        message = 'そろそろ移動したほうがええんちゃう？'

        line_bot_api.push_message(user_id, TextMessage(text=message))

def send_auth_url(user_id):
    auth_url = 'http://your-domain.com/auth/google/'  # Google認証のURL
    
    message = TextSendMessage(text='Google認証を行うために以下のリンクをクリックしてください: {}'.format(auth_url))
    line_bot_api.push_message(user_id, message)


# def today_schedule(calendar_id: str)-> tuple:
def today_schedule(calendar_id: str) -> tuple:
    """今日のスケジュールを文字列とリストで取得する関数"""
    # GoogleカレンダーAPIのスコープ
    scopes = ["https://www.googleapis.com/auth/calendar.readonly"]

    # 認証情報を読み込む
    credentials_dict = json.loads(CREDENTIALS)
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
        schedule += "今日の予定はないで～"

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
        openai.api_key = CHATGPT_API_KEY
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "関西弁で話して"},
                {"role": "system", "content": "発言の最後に「知らんけど。」をつけて"},
                {"role": "system", "content": "アドバイスをください"},
                {"role": "user", "content": f"{schedule}"},
            ],
        )

        message = response.choices[0]["message"]["content"].strip()
        schedule += "=============\n"
        schedule += message

    return (schedule, event_list)


def food_suggest(vege_list: list) -> str:
    food = " ".join(vege_list)
    openai.api_key = CHATGPT_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "関西弁で話して"},
            {"role": "system", "content": "発言の最後に「知らんけど。」をつけて"},
            {"role": "user", "content": f"{food}を使った料理を提案してほしい。"},
        ],
    )

    message = response.choices[0]["message"]["content"].strip()
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

                    if rain_probability >= 0:
                        weather = f"(株)サポーターズで雨が降りそうやで！傘持っててな！"
                        break

        if weather != None:
            break
    if weather == None:
        weather = "今日は雨は降らんで～"
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

def get_food_ingredients(image_path):
    name = [line.rstrip('\n').lower() for line in open(VOCAB_TXT)]
    credentials_dict = json.loads(CREDENTIALS)
    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict
    )
    client = vision.ImageAnnotatorClient(credentials=credentials)
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    objects = client.object_localization(image=image).localized_object_annotations
    vege_list = [object_.name for object_ in objects if object_.name.lower() in name]
    print(objects)
    return vege_list


def index(request):
    return HttpResponse("This is bot api.")
