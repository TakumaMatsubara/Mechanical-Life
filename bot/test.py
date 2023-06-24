# # %%
# import pathlib
# from django.shortcuts import redirect, render
# from django.http import HttpResponseForbidden, HttpResponse, HttpResponseBadRequest
# from django.views.decorators.csrf import csrf_exempt
# from httplib2 import Http
# from linebot import LineBotApi, WebhookHandler
# from linebot.exceptions import InvalidSignatureError, LineBotApiError
# from linebot.models import (
#     MessageEvent,
#     TextMessage,
#     TextSendMessage,
#     ImageMessage
# )
# import pydata_google_auth
# import os, io
# import urllib.request, json
# import urllib.parse
# import datetime
# import requests
# import pytz
# import logging
# from google.oauth2 import service_account
# from googleapiclient.discovery import build
# from google_auth_oauthlib.flow import Flow
# from google.auth.transport.requests import Request
# import openai
# import tempfile
# import cv2
# from google.cloud import vision_v1p3beta1 as vision


# # CREDENTIALS = {
# #     "type": "service_account",
# #     "project_id": "mechanical-life-matsubara",
# #     "private_key_id": "b1f1c2f55dcb22573378f4468e306edf0386f5e1",
# #     "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCwWJNB9Yhws4zk\nI6HpIEZpSfMfaAkVfqPIPLW19sGEyTrYtuePF0DTbC8HtsvYRbvZ4fOrzM1Fwwt6\nKitg2c6XUX9x48IUSQBvw1T4tkYyVIpQE10T2ZgZUSC7lpb6hB/cigh6f0N0FD1r\nrqzoaOztDrblMgjNAlGVCknZxyFqnV6Hvy5u8YbW5C5V9k3kufraS42V57CqbCPL\nqOPEIcQs7WcgGa2xA+8qWC4MMgaLs77rtL/PrDXlnTC/dWn7celwznt2GfB6Qh71\neejvjh7D3MRl7vznPwoCQTN/X8rh6ORL807Yhmn/+kcKgWjQNNAge46le8pMH6C9\nodBYFNGdAgMBAAECggEAEQ8jK7HOFvefl7WaD5x3g0RL7cwEI51XyGKVwiUSl78E\nX3uOJKmqCT8sFjHI6sKQMhB+yy3+5j1AinsILZB/Fjn5kLG+Osp3GC4MCxqi6XKD\n23bhaFlX3Tcbv1ne1XGGSDDdh3Ab59+fXh/h39e/97dr2k8qn8kWIvYBqpIYuaCX\ndRh6mtjeE0CUE2SO4OKvdubrvUBA5KzxBtO3RDYTM4nNVuwcSjVkyR6i6kTl+Iv0\njEPoIwqedAmuVS5FlKajaq5joevKJ0rrrVJW+1AVpTvgmdQl1aOMHQ4EHDzIL3KL\nxaw5KPc7IzpSae+IHyGhCDKBYl16OuaAZ8ir18YSNwKBgQDfe3aUxf4sAXZo5+Tk\naY4vjzJ9YZ4cJsevjFpY+QllmnWHrf5E+tGYBoZ7bkjf7WeKm9i5go9VPQzxC9ty\n46/r7fiFPUhyMIu23a7/xLT6gJC08W4c1Zg+BIGvvVDO1BPixUKbYXz6ljC8vJYX\nWFAMkXHN9zMyMXQpb++f2Hk0BwKBgQDKAVK2xiH56TxK/k/hvZmEr6JhxVaHiPjy\nbfEzb1vvTTJnlwlG2OU/zMpvSaOpS7RD+GfiIvrUvzKSyA5jplfBac7qljnrMDya\nTUuAOmKMZVDmLcZ0yfgT2W2azffX7NpOmGIn7q3nZyTfisRJ/dRSoy+eY+jwEAir\nheNOXj6MOwKBgQCFZl1SUR13hyf3VvT6o0eMfB3XWf3XMA7iaxVDJuTFEX42j1XI\nNzAFX1/HLf2yLTQxOPYVRino55hiCoHkAqVwX4yJfBtSjkfX0Fw1sGWXYkb+u17P\nN3C5FFeVX5xs2YtFQhqQRZEkw6I0Bx5QsRaXafpUx8p3m62LTpXrBHzU4QKBgF+j\nSLnoDGX5muYWiVNjJK/BR6vqdhEtNE/y5WNosaoWbmrFA0tbnQ4bsywFPUsF4I7d\nqLFTxlW7QAJmXQmo05tqsOA3x6wl5ktXlQtcmRPHVAnmWjMo/B7Jri7AnTrJlIHp\ne29UfVk1aCu90zkEx+VoBT+EJeCidrheZ0PPMuXJAoGAedSLNe/VyY5Ul40D27L3\ndcGnOKQ+TZnxIqPDr/D5qFfQfkf8Dc99H+O82VlYv194EPI8JfOeB6z97xi0pLwg\nOQnkQbJeVCQaXh8Cneg/ZSdA0LpknkTvpd7eHzED3xDMDrUgomCmNY001r3fa+yG\nSWTiPxxDsaQOfkOex7qrGmg=\n-----END PRIVATE KEY-----\n",
# #     "client_email": "mechanical-life-578@mechanical-life-matsubara.iam.gserviceaccount.com",
# #     "client_id": "105374612739214989666",
# #     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
# #     "token_uri": "https://oauth2.googleapis.com/token",
# #     "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
# #     "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/mechanical-life-578%40mechanical-life-matsubara.iam.gserviceaccount.com",
# #     "universe_domain": "googleapis.com"
# # }

# CREDENTIALS = "../credentials.json"
# name = [line.rstrip('\n').lower() for line in open('../vege.txt')]
# with open(CREDENTIALS) as f:
#     credentials_dict = json.load(f)
# credentials = service_account.Credentials.from_service_account_info(
#     credentials_dict
# )
# client = vision.ImageAnnotatorClient(credentials=credentials)
# image_path = os.path.join(parent_dir, "food.jpg")
# with io.open(image_path, 'rb') as image_file:
#     content = image_file.read()
# image = vision.types.Image(content=content)
# response = client.object_localization(image=image)
# labels = response.localized_object_annotations
# image = vision.Image()

# current_dir = os.getcwd()
# parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
# # image_path = pathlib.Path(image_path).as_uri()
# # image_path = image_path.replace("file:///", "")
# image_path = "https://dime.jp/genre/files/2019/10/a2fdf4b7485126201225f13050b05a7a.jpg"
# image.source.image_uri = image_path

# response = client.label_detection(image=image)
# labels = response.label_annotations
# text_list = []
# for label in labels:
#     desc = label.description.lower()
#     if desc in name:
#         text_list.append(desc)

# print(text_list)

# %%
from google.cloud import vision
# from google.cloud import translate_v2 as translate
file_path = '../food.jpg'
credentials_file = '../credentials.json'
target_language = "ja"
# 認証情報の設定
name = [line.rstrip('\n').lower() for line in open('../vege.txt')]

client = vision.ImageAnnotatorClient.from_service_account_json(credentials_file)

with open(file_path, 'rb') as image_file:
    content = image_file.read()

image = vision.Image(content=content)

# 物体検出のリクエストを作成
objects = client.object_localization(image=image).localized_object_annotations
# translate_client = translate.Client()# 物体の検出結果を表示
vege_list = [object_.name for object_ in objects if object_.name.lower() in name]
# trans_vege_list = [translator.translate(vege, dest="ja").text for vege in vege_list]
for object_ in objects:
    print(f'物体名: {object_.name}')
    print(f'信頼度: {object_.score}')
    print('------')
print(vege_list)
# print(trans_vege_list)



# ローカルファイルのパスとサービスアカウントキーファイルのパスを指定して物体認識を実行
file_path = '../food.jpg'
credentials_file = '../credentials.json'

# %%
