import base64
import hmac
import json
import wave
from chat import *
import configparser
import urllib
import hashlib
from dataclasses import dataclass
import time
import os
import requests
# from bark import SAMPLE_RATE, generate_audio
# from scipy.io.wavfile import write as write_wav


# def text_to_speech(text_prompt, audio_file_name):
#     """
#     文本转音频，并保存音频
#     """

#     audio_array = generate_audio(text_prompt)
#     write_wav("./{audio_file_name}.wav", SAMPLE_RATE, audio_array)


def speech_to_text(files, audio_file_name):
    """
    语音转文本，并保存语音
    """
    audio_file = files['audio']
    audio_file.save(f'static/{audio_file_name}.mp3')
    audio_file = open(f'static/{audio_file_name}.mp3', 'rb')
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return transcript.text


class Authorization:
    AppId = 0
    SecretId = ""
    SecretKey = ""
    Expired = 3600
    conf = configparser.ConfigParser()

    def init(self):
        # print("init")
        self.conf.read("./envs/tcloud_auth.ini", encoding="UTF-8")
        self.AppId = self.conf.getint("authorization", "AppId")
        self.SecretId = self.conf.get("authorization", "SecretId")
        self.SecretKey = self.conf.get("authorization", "SecretKey")
        # print(self)

    def generate_sign(self, request_data):
        url = "tts.cloud.tencent.com/stream"
        sign_str = "POST" + url + "?"
        sort_dict = sorted(request_data.keys())
        for key in sort_dict:
            if isinstance(request_data[key], float):
                sign_str = sign_str + key + "=" + urllib.parse.unquote(
                    '%g' % (request_data[key])) + '&'
            else:
                sign_str = sign_str + key + "=" + urllib.parse.unquote(
                    str(request_data[key])) + '&'
        sign_str = sign_str[:-1]
        sign_bytes = sign_str.encode('utf-8')
        key_bytes = self.SecretKey.encode('utf-8')
        # print(sign_bytes)
        authorization = base64.b64encode(
            hmac.new(key_bytes, sign_bytes, hashlib.sha1).digest())
        return authorization.decode('utf-8')


class Request:
    Text = "你好"
    Action = "TextToStreamAudio"
    Codec = "pcm"
    Expired = 0
    ModelType = 0
    PrimaryLanguage = 1
    ProjectId = 0
    SampleRate = 16000
    SessionId = "123"
    Speed = 0
    VoiceType = 1017
    Volume = 5
    conf = configparser.ConfigParser()

    def init(self, text: str):
        # print("init")
        self.conf.read("./envs/request_parameter.ini", encoding="UTF-8")
        # self.Text = self.conf.get("parameter", "Text")
        self.Text = text
        self.Action = self.conf.get("parameter", "Action")
        self.Codec = self.conf.get("parameter", "Codec")
        self.Expired = self.conf.getint("parameter", "Expired")
        self.ModelType = self.conf.getint("parameter", "ModelType")
        self.PrimaryLanguage = self.conf.getint("parameter", "PrimaryLanguage")
        self.ProjectId = self.conf.getint("parameter", "ProjectId")
        self.SampleRate = self.conf.getint("parameter", "SampleRate")
        self.SessionId = self.conf.get("parameter", "SessionId")
        self.Speed = self.conf.getfloat("parameter", "Speed")
        self.VoiceType = self.conf.getint("parameter", "VoiceType")
        # self.VoiceType = 1017
        self.Volume = self.conf.getfloat("parameter", "Volume")
        # print(self)


def openai_speech(text, save_path):

    speech_file_path = save_path
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
        speed=0.85
    )
    response.stream_to_file(speech_file_path)
    with open(save_path, 'rb') as f:
        audio_base64 = base64.b64encode(f.read()).decode('utf-8')
    return audio_base64


def text_to_speech(text, save_path):
    req = Request()
    req.init(text)
    auth = Authorization()
    auth.init()
    request_data = dict()
    request_data['Action'] = 'TextToStreamAudio'
    request_data['AppId'] = auth.AppId
    request_data['Codec'] = req.Codec
    request_data['Expired'] = int(time.time()) + auth.Expired
    request_data['ModelType'] = req.ModelType
    request_data['PrimaryLanguage'] = req.PrimaryLanguage
    request_data['ProjectId'] = req.ProjectId
    request_data['SampleRate'] = req.SampleRate
    request_data['SecretId'] = auth.SecretId
    request_data['SessionId'] = req.SessionId
    request_data['Speed'] = req.Speed
    request_data['Text'] = req.Text
    request_data['Timestamp'] = int(time.time())
    request_data['VoiceType'] = req.VoiceType
    request_data['Volume'] = req.Volume
    signature = auth.generate_sign(request_data=request_data)
    header = {"Content-Type": "application/json", "Authorization": signature}
    url = "https://tts.cloud.tencent.com/stream"

    r = requests.post(url,
                      headers=header,
                      data=json.dumps(request_data),
                      stream=True)

    if str(r.content).find("Error") != -1:
        print(r.content)
        return

    i = 1
    wavfile = wave.open(save_path, 'wb')
    wavfile.setparams((1, 2, 16000, 0, 'NONE', 'NONE'))
    for chunk in r.iter_content(1000):
        if (i == 1) & (str(chunk).find("Error") != -1):
            # print(chunk)
            return
        i = i + 1
        wavfile.writeframes(chunk)
    wavfile.close()

    with open(save_path, 'rb') as f:
        audio_base64 = base64.b64encode(f.read()).decode('utf-8')
    return audio_base64


# text_to_speech("我是一个小猪", "test.mp3")
