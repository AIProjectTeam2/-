from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, AudioMessage
import openai
import os
import requests
import speech_recognition as sr
from pydub import AudioSegment

load_dotenv()

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
openai.api_key = os.getenv('OPENAI_API_KEY')
CHAT_MODEL = os.getenv('CHAT_COMPLETION_MODEL', 'gpt-3.5-turbo')


@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info('Request body: ' + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print('Invalid signature. Please check your channel access token/channel secret.')
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_text = event.message.text
    messages = [
        {'role': 'system', 'content': '假設你現在是個健康助理'},
        {'role': 'system', 'content': '你只能依情況回復: 1. 分析症狀 2. 提供建議 3. 必要時提示就醫 4. 當對方說的在前三項以外，只能說今天天氣很好。'},
        {'role': 'system', 'content': '只能回覆50個字左右，並且以條列式重點列出。'},
        {'role': 'user', 'content': user_text}
    ]
    response = openai.ChatCompletion.create(
        model=CHAT_MODEL,
        messages=messages
    )
    content = response['choices'][0]['message']['content']

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=content.strip()))


@handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    audio_file_path = f'/tmp/{event.message.id}.m4a'

    with open(audio_file_path, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)

    wav_file_path = f'/tmp/{event.message.id}.wav'
    audio = AudioSegment.from_file(audio_file_path)
    audio.export(wav_file_path, format='wav')

    text = audio_to_text(wav_file_path)
    handle_text_message_with_text(event.reply_token, text)


def handle_text_message_with_text(reply_token, text):
    messages = [
        {'role': 'system', 'content': '假設你現在是個健康助理'},
        {'role': 'system', 'content': '你只能依情況回復: 1. 分析症狀 2. 提供建議 3. 必要時提示就醫 4. 當對方說的在前三項以外，只能說今天天氣很好。'},
        {'role': 'system', 'content': '只能回覆50個字左右，並且以條列式重點列出。'},
        {'role': 'user', 'content': text}
    ]
    response = openai.ChatCompletion.create(
        model=CHAT_MODEL,
        messages=messages
    )
    content = response['choices'][0]['message']['content']

    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(text=content.strip()))


def audio_to_text(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio, language='zh-TW')
        return text
    except sr.UnknownValueError:
        return "無法識別語音"
    except sr.RequestError as e:
        return f"語音服務請求錯誤; {e}"


@app.route('/', methods=['GET'])
def home():
    return 'Hello World!'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)