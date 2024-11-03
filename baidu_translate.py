import requests
import random
import json
import os
from hashlib import md5
from srt_extract import extract_subtitles_from_srt_text
from dotenv import load_dotenv

load_dotenv('environment.env')


def baidu_trans_to_en(file_path):
    # Set your own appid/appkey.
    appid = os.getenv("baidu_translate_appid")
    appkey = os.getenv("baidu_translate_appkey")
    from_lang = 'auto'
    to_lang = 'en'
    endpoint = 'http://api.fanyi.baidu.com'
    path = '/api/trans/vip/translate'
    url = endpoint + path

    query = extract_subtitles_from_srt_text(file_path)

    # Generate salt and sign
    def make_md5(s, encoding='utf-8'):
        return md5(s.encode(encoding)).hexdigest()

    salt = random.randint(32768, 65536)
    sign = make_md5(appid + query + str(salt) + appkey)

    # Build request
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {'appid': appid, 'q': query, 'from': from_lang, 'to': to_lang, 'salt': salt, 'sign': sign}

    # Send request
    r = requests.post(url, params=payload, headers=headers)
    result = r.json()
    trans_result = result.get('trans_result', [])
    # 中英双语句句对照
    srt = []
    for i in trans_result:
        src_text = i.get('src', '')
        dst_text = i.get('dst', '')
        srt.append(f"{src_text}\n{dst_text}\n")
    return "\n".join(srt)


def baidu_trans_to_zh(file_path):
    # Set your own appid/appkey.
    appid = os.getenv("baidu_translate_appid")
    appkey = os.getenv("baidu_translate_appkey")
    from_lang = 'auto'
    to_lang = 'zh'
    endpoint = 'http://api.fanyi.baidu.com'
    path = '/api/trans/vip/translate'
    url = endpoint + path

    query = extract_subtitles_from_srt_text(file_path)

    # Generate salt and sign
    def make_md5(s, encoding='utf-8'):
        return md5(s.encode(encoding)).hexdigest()

    salt = random.randint(32768, 65536)
    sign = make_md5(appid + query + str(salt) + appkey)

    # Build request
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {'appid': appid, 'q': query, 'from': from_lang, 'to': to_lang, 'salt': salt, 'sign': sign}

    # Send request
    r = requests.post(url, params=payload, headers=headers)
    result = r.json()
    trans_result = result.get('trans_result', [])  # 读取json格式内容
    # 中英双语句句对照
    srt = []
    for i in trans_result:
        src_text = i.get('src', '')
        dst_text = i.get('dst', '')
        srt.append(f"{src_text}\n{dst_text}\n")
    return "\n".join(srt)



