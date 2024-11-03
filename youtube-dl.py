import yt_dlp as youtube_dl
import os
from dotenv import load_dotenv

load_dotenv('environment.env')


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


if __name__ == "__main__":
    video_url = "https://youtu.be/4b6MddCvs-0?si=PT6ctyX36OdAmnK_"
    video_title = download_video(video_url)
    print(video_title)
