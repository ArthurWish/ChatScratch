import base64
import hmac
import json
import wave
import openai
import configparser
import urllib
import hashlib
from dataclasses import dataclass
import time

import requests

def speech_to_text(files):
    audio_file = files['audio']
    audio_file.save('static/audio.wav')
    audio_file = open('static/audio.wav', 'rb')
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    content = transcript["text"]
    with open("speech_to_text.txt", "+a") as f:
        f.write("\n")
        f.write(content)
    return content


class Authorization:
    AppId = 0
    SecretId = ""
    SecretKey = ""
    Expired = 3600
    conf = configparser.ConfigParser()

    def init(self):
        print("init")
        self.conf.read("./envs/tcloud_auth.ini", encoding="UTF-8")
        self.AppId = self.conf.getint("authorization", "AppId")
        self.SecretId = self.conf.get("authorization", "SecretId")
        self.SecretKey = self.conf.get("authorization", "SecretKey")
        print(self)

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
        print(sign_bytes)
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
    VoiceType = 101016
    Volume = 5
    conf = configparser.ConfigParser()

    def init(self, text: str):
        print("init")
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
        self.Volume = self.conf.getfloat("parameter", "Volume")
        print(self)


def text_to_speech(text):
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
    signature = auth.generate_sign(request_data = request_data)
    header = {
        "Content-Type": "application/json",
        "Authorization": signature
    }
    url = "https://tts.cloud.tencent.com/stream"

    r = requests.post(url, headers=header, data=json.dumps(request_data), stream = True)
    '''
    if str(r.content).find("Error") != -1 :
        print(r.content)
        return
    '''
    i = 1
    wavfile = wave.open('test.wav', 'wb')
    wavfile.setparams((1, 2, 16000, 0, 'NONE', 'NONE'))
    for chunk in r.iter_content(1000):
        if (i == 1) & (str(chunk).find("Error") != -1) :
            print(chunk)
            return 
        i = i + 1
        wavfile.writeframes(chunk)
        
    wavfile.close()

# text_to_speech("我是一个小猪")