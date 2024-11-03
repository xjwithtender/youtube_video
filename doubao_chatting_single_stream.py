from openai import OpenAI
import yt_dlp as youtube_dl
import os
from dotenv import load_dotenv

load_dotenv('environment.env')
client = OpenAI(
    api_key=os.getenv("API_KEY_OPENAI"),
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)


# 下载youtube视频
def download_video(url):
    proxy = os.getenv("proxy")
    ydl_opts = {
        'proxy': proxy,
        'outtmpl': '%(title)s.%(ext)s'  # 设置下载视频的文件名为视频标题
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        # 获取视频信息
        info_dict = ydl.extract_info(url, download=False)
        video_title = info_dict.get('title', None)
        # 下载视频
        ydl.download([url])
        return video_title


def doubao_streaming(user_input, history):
    client = OpenAI(
        api_key=os.getenv("API_KEY_OPENAI"),
        base_url="https://ark.cn-beijing.volces.com/api/v3",
    )
    # messages = [{"role": "system",
    # "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手。我将输入一些音频和视频内容作为我们对话的基础：" + text_str}]
    # history.append({"role": "user", "content": user_input})
    stream = client.chat.completions.create(
        model=os.getenv("chat_model"),
        messages=history,
        stream=True
    )
    # 初始化一个空的字符串
    full_content = ""
    for chunk in stream:
        if not chunk.choices:
            continue
        full_content += chunk.choices[0].delta.content
    return full_content
