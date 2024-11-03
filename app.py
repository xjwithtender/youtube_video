import streamlit as st
import yt_dlp
import os
import doubao_api_ch
import doubao_chatting_single_stream
import faiss_openai
from openai import OpenAI
from srt_extract import extract_subtitles_from_srt_text
import sqlite3
from dotenv import load_dotenv

load_dotenv('environment.env')

client = OpenAI(
    api_key=os.getenv("API_KEY_OPENAI"),
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)


# 初始化sqlite数据库
def init_db():
    db_path = "youtube_video.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_url TEXT UNIQUE,
        file_path TEXT,
        title TEXT
        )
    ''')
    conn.commit()
    conn.close()


# 插入视频信息
def insert_video_info(video_url, file_path, title):
    conn = sqlite3.connect("youtube_video.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO videos (video_url, file_path, title)
        VALUES (?, ?, ?) 
        ''', (video_url, file_path, title)
                   )
    conn.commit()
    conn.close()


# 检查视频信息是否存在
def is_video_in_db(video_url):
    conn = sqlite3.connect("youtube_video.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE video_url = ?", (video_url,))
    video = cursor.fetchone()
    conn.close()
    return video  # 不存在视频url的话返回None


def download_video(url, output_dir):
    # 检查数据库中是否已经存在该视频
    existing_video = is_video_in_db(url)
    if existing_video:
        st.write(f"视频已存在，路径为: {existing_video[2]}")
        return
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'proxy': os.getenv("proxy")
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True) # 下载视频信息
        video_title = info_dict.get('title', None)
        video_extension = info_dict.get('ext', None)
        file_path = os.path.join(output_dir, f"{video_title}.{video_extension}")
        # 将视频信息存储到数据库中
        insert_video_info(url, file_path, video_title)
        st.success(f"视频 '{video_title}' 下载完成，路径: {file_path}")


def download_audio(url, output_dir):
    # 检查数据库中是否已经存在该视频
    existing_video = is_video_in_db(url)
    if existing_video:
        st.write(f"视频已存在，路径为: {existing_video[2]}")
        return
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'proxy': os.getenv("proxy")
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True) # 下载视频信息
        video_title = info_dict.get('title', None)
        video_extension = info_dict.get('ext', None)
        file_path = os.path.join(output_dir, f"{video_title}.{video_extension}")
        # 将视频信息存储到数据库中
        insert_video_info(url, file_path, video_title)
        st.success(f"视频 '{video_title}' 下载完成，路径: {file_path}")


# 播放视频
def play_video(file_path):
    st.video(file_path)


# 更新视频库
def update_video_library(output_dir):
    videos = [f for f in os.listdir(output_dir) if f.endswith(('.mp4', '.mkv', '.avi'))]
    return videos


# 删除视频
def delete_video(file_path):
    os.remove(file_path)


def main():
    st.title("Youtube视频下载")

    # 用户输入
    url_input = st.text_area("输入要下载的链接（使用空格键分隔多个链接）")
    download_video_option = st.checkbox("下载最佳品质的MP4视频文件")
    download_audio_option = st.checkbox("下载最佳品质的MP3音频文件")
    download_button = st.button("开始下载")

    output_dir = "downloads"
    # 定义字幕保存文件
    subtitle_store_path = "subtitles.txt"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if download_button:
        if not url_input:
            st.error("请输入至少一个下载链接。")
        else:
            urls = url_input.split()
            output_dir = "downloads"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            for url in urls:
                st.write(f"正在下载：{url}")
                if download_video_option:
                    try:
                        download_video(url, output_dir)
                        st.success(f"视频下载完成：{url}")
                        # 询问用户是否要播放视频
                        if st.button(f"播放 {url}"):
                            video_path = os.path.join(output_dir, f'{url}.mp4')
                            play_video(video_path)
                    except Exception as e:
                        st.error(f"视频下载失败：{url} 错误信息：{e}")

                if download_audio_option:
                    try:
                        download_audio(url, output_dir)
                        st.success(f"音频下载完成：{url}")
                    except Exception as e:
                        st.error(f"音频下载失败：{url} 错误信息：{e}")
    # 文本faiss检索
    st.header("文本检索(相似度最高的三句视频文本）")
    text_searching = st.text_area("输入要查找的文本关键词:")
    text_searching_button = st.button("开始查找")
    if text_searching_button:
        if not text_searching:
            st.error("请输入至少一个关键词。")
        else:
            if "full_srts" not in st.session_state or not st.session_state.full_srts:
                st.error("请先加载字幕")
            else:
                # 从字幕文件中检索关键词
                with open(subtitle_store_path, "r", encoding="utf-8") as f:
                    subtitle_lines = f.readlines()
                embedding_dim, embeddings = faiss_openai.faiss_embeddings(subtitle_lines)
                query_text = text_searching
                search_text = faiss_openai.faiss_searching(embedding_dim, embeddings, query_text, subtitle_lines)
                # 获取对应视频标题
                if search_text:
                    st.write("检索结果：")
                    st.write("\n".join(search_text))
                else:
                    st.write("没有找到相关字幕内容。")

    st.header("视频库")
    videos = update_video_library(output_dir)
    if videos:
        for video in videos:
            video_path = os.path.join(output_dir, video)
            st.video(video_path)

            # 添加删除视频和查看字幕按钮
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button(f"删除 {video}"):
                    delete_video(video_path)
                    st.warning(f"{video} 已删除。")
            with col2:
                if st.button(f"查看字幕 {video}"):
                    subtitle_file = doubao_api_ch.convert_video_to_srt(video_path)[0]  # 0-代表中文原版字幕文件，1-代表中英双语字幕文件
                    if os.path.exists(subtitle_file):
                        with open(subtitle_file, 'r', encoding='utf-8') as f:
                            subtitles = f.read()
                            st.text_area(f"字幕内容：{video}", subtitles, height=300)
                        # 存储本地的字幕文本文件和索引
                        with open(subtitle_file, 'r', encoding='utf-8') as f:
                            subtitles_readlines = f.readlines()
                        clean_subtitles = []
                        for line in subtitles_readlines:
                            if "-->" not in line and not line.strip().isdigit():
                                clean_subtitles.append(line.strip())
                        subtitles_text = "\n".join(clean_subtitles)
                        st.session_state.full_srts = clean_subtitles  # 存储到 session_state
                        # 将字幕内容和索引写入本地文件
                        with open(subtitle_store_path, "r",
                                  encoding="utf-8") as f:
                            existing_content = f.read()
                        if f"视频标题: {video}" not in existing_content:
                            with open(subtitle_store_path, "a", encoding="utf-8") as f:
                                # 参数"a"以追加模式打开文件。如果文件已经存在，新的内容将被添加到文件的末尾，而不是覆盖原有的内容
                                # 写入视频标题作为索引
                                f.write(f"\n视频标题: {video} \n")
                                # 将字幕作为整体写入，保留其原有格式
                                f.write(f"{subtitles_text}\n")
                    else:
                        st.warning(f"{video} 没有可用的字幕。")
            with col3:  # 重新设计逻辑
                if st.button(f"对话 {video}"):
                    if "messages" not in st.session_state:
                        st.session_state.messages = []
                    subtitle_file = doubao_api_ch.convert_video_to_srt(video_path)[0]
                    text_str = extract_subtitles_from_srt_text(subtitle_file)
                    # 构建输入框让用户输入对话内容
                    user_input = st.text_input("请输入对话内容：")
                    # submit_button = st.button("发送")
                    # st.write(submit_button)
                    st.write(user_input)
                    if st.button("发送") and user_input:
                        st.write(user_input)
                        # 把用户输入添加到对话历史中
                        st.session_state.messages.append({"role": "system",
                                                          "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手。我将输入一些音频和视频内容作为我们对话的基础：" + text_str})
                        st.session_state.messages.append({"role": "user", "content": user_input})
                        # 调用模型生成新对话，并更新对话历史
                        st.write(st.session_state)
                        response = doubao_chatting_single_stream.doubao_streaming(text_str, user_input,
                                                                                  st.session_state.messages)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    # 立即在用户输入框下方显示对话历史
                    for message in st.session_state.messages:
                        if message["role"] == "user":
                            st.write(f"用户: {message['content']}")
                        else:
                            st.write(f"豆包: {message['content']}")
    else:
        st.info("视频库为空。")


if __name__ == "__main__":
    init_db()
    main()
    # 运行在终端输入 streamlit run app.py
