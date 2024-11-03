import requests
import time
import subprocess
from datetime import timedelta
import baidu_translate
import os
from dotenv import load_dotenv


# 视频转为字幕功能（中文视频）
# 视频字幕功能整体处理流程分为三个阶段：
# 1.客户端抽取视频中音轨，转成音频文件；
# 2.把音频文件发送至后端集群，获取任务 ID；
# 3.通过任务 ID 访问后端接口获取结果。

#  固定：
load_dotenv('environment.env')
base_url = 'https://openspeech.bytedance.com/api/v1/vc'
appid = os.getenv("doubao_appid") # API-key管理-名称  用于标识当前应用
access_token = os.getenv("doubao_accesstoken")  # API key

# 音视频的发声语音-中文

language = 'zh-CN'


def log_time(func):
    def wrapper(*args, **kw):
        begin_time = time.time()
        func(*args, **kw)
        print('total cost time = {time}'.format(time=time.time() - begin_time))

    return wrapper


# 将毫秒转为字幕格式时间值
def ms_to_time_string(*, ms=0, seconds=None):
    # 计算小时、分钟、秒和毫秒
    if seconds is None:
        td = timedelta(milliseconds=ms)
    else:
        td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000

    time_string = f"{str(hours).zfill(2)}:{str(minutes).zfill(2)}:{str(seconds).zfill(2)},{str(milliseconds).zfill(3)}"
    return time_string


def convert_video_to_srt(file_url):
    basename = os.path.basename(file_url)
    # 将视频文件转换为音频文件（ffmepg）-wav文件
    subprocess.run(["ffmpeg", "-y", '-i', file_url, "-ac", "1", "-ar", "24000", basename + ".wav"])  # 1通道 24k

    with open(basename + ".wav", 'rb') as f:
        audio = f.read()  # 以二进制方式

    response = requests.post(
        '{base_url}/submit'.format(base_url=base_url),
        params=dict(
            appid=appid,  # API-key管理-名称  用于标识当前应用
            language=language,  # 字幕语言类型
            use_itn='True',  # 将识别结果中的中文数字自动转成阿拉伯数字
            use_capitalize='True',
            max_lines=1,  # 每屏最多展示行数
            words_per_line=15,  # 每行最多展示字数
        ),
        data=audio,
        headers={
            'content-type': 'audio/wav',
            'Authorization': 'Bearer; {}'.format(access_token)
        }
    )
    print('submit response = {}'.format(response.text))
    assert (response.status_code == 200)
    assert (response.json()['message'] == 'Success')

    # 返回结果
    job_id = response.json()['id']
    response = requests.get(
        '{base_url}/query'.format(base_url=base_url),
        params=dict(
            appid=appid,
            id=job_id,
        ),
        headers={
            'Authorization': 'Bearer; {}'.format(access_token)
        }
    )
    print('query response = {}'.format(response.json()))
    assert (response.status_code == 200)
    result = response.json()
    assert (result['code'] == 0)

    # 获取原中文字幕，生成无翻译版字幕文件（srt_file_non_translate.srt)
    srts = []
    for i, it in enumerate(response.json()['utterances']):
        srts.append(
            f'{i + 1}\n{ms_to_time_string(ms=it["start_time"])} --> {ms_to_time_string(ms=it["end_time"])}\n{it["text"]}\n\n')
    srt_file = os.path.splitext(basename)[0] + '_non_translate.srt'
    with open(f'./{srt_file}', 'w', encoding='utf-8') as f:
        f.write("".join(srts))

    # 原中文字幕文件放入百度翻译api，生成双语翻译版字幕文件(srt_file_lan_translate.srt)
    srts_lan = baidu_translate.baidu_trans_to_en(file_path=srt_file)
    bilingual_lines = srts_lan.strip().split("\n\n")
    utterances = response.json()['utterances']
    srts = []
    for i, utterance in enumerate(utterances):
        if i < len(bilingual_lines):  # 确保时间和字幕数量一致
            # 提取中英文字幕
            bilingual_subtitle = bilingual_lines[i].split("\n")
            chinese_text = bilingual_subtitle[0]
            english_text = bilingual_subtitle[1] if len(bilingual_subtitle) > 1 else ""
            # 加入到字幕列表中
            srts.append(
                f'{i + 1}\n{ms_to_time_string(ms=utterance["start_time"])} --> {ms_to_time_string(ms=utterance["end_time"])}\n{chinese_text}\n{english_text}\n\n')
    srt_file_lan = os.path.splitext(basename)[0] + '_translate.srt'
    with open(f'./{srt_file_lan}', 'w', encoding='utf-8') as f:
        f.write("".join(srts))

    return os.path.abspath(srt_file), os.path.abspath(srt_file_lan)



