from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
openai.api_key = os.getenv('OPENAI_API_KEY')

@csrf_exempt
def callback(request):
    signature = request.headers['X-Line-Signature']
    body = request.body.decode('utf-8')

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return JsonResponse({'status': 'Invalid signature'}, status=400)

    return JsonResponse({'status': 'ok'})

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    response_message = get_gpt_response(user_message)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_message))

def get_gpt_response(user_message):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"你是一個醫療助理。當用戶描述症狀時，建議合適的掛號科別。用戶症狀：{user_message}",
        max_tokens=100
    )
    return response.choices[0].text.strip()
