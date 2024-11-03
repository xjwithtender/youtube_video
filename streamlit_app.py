import streamlit as st
import os
import yt_dlp
import sqlite3
from openai import OpenAI
import doubao_api_ch
import doubao_chatting_single_stream
import faiss_openai
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
from milvus import default_server
import re
from dotenv import load_dotenv

load_dotenv('environment.env')

client = OpenAI(
    api_key=os.getenv("API_KEY_OPENAI"),
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)


# Introduction
def intro():
    st.write("# 🌟 欢迎来到我们的YouTube视频下载任务！ 👋")
    st.sidebar.success("在这挑选您需要的功能")
    st.markdown(
        '''
        YouTube是全球最大的视频分享平台，于2005年成立，总部位于美国加利福尼亚州。
        用户可以在YouTube上上传、观看、分享和评论各种类型的视频，包括娱乐、教育、新闻、音乐、游戏等多种内容。
        它提供了一个开放的平台，让用户可以自由创作内容并与全球观众互动。
        由于其庞大的用户基础和多样化的视频资源，YouTube已经成为获取信息、娱乐和教育的重要渠道之一。
        
        **👈 选择一个您想要实现的功能吧！
         
        ### YouTube视频任务：
          
        - 音视频下载
        - 音视频库管理
        - 音视频字幕文本检索
        - 音视频字幕文本对话
        '''
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
        title TEXT,
        subtitles TEXT
        )
    ''')
    conn.commit()
    conn.close()


# 插入视频信息
def insert_video_info(video_url, file_path, title, subtitles):
    init_db()
    conn = sqlite3.connect("youtube_video.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO videos (video_url, file_path, title, subtitles)
        VALUES (?, ?, ?, ?) 
        ''', (video_url, file_path, title, subtitles)
                   )
    conn.commit()
    conn.close()


# 检查视频信息是否存在
def is_video_in_db(video_url):
    init_db()
    conn = sqlite3.connect("youtube_video.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE video_url = ?", (video_url,))
    video = cursor.fetchone()
    conn.close()
    return video  # 不存在视频url的话返回None


def video_Download(url, output_dir):
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
        info_dict = ydl.extract_info(url, download=True)  # 下载视频信息
        video_title = info_dict.get('title', None)
        video_extension = info_dict.get('ext', None)
        clean_video_title = re.sub(r'[\\/*?:"<>|]', "", video_title)
        file_path = os.path.join(output_dir, f"{clean_video_title}.{video_extension}")
        subtitle_file = doubao_api_ch.convert_video_to_srt(file_path)[1]  # 0-代表中文原版字幕文件，1-代表中英双语字幕文件
        if os.path.exists(subtitle_file):
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                subtitles = f.read()
        # 将视频信息存储到数据库中

        with open(subtitle_file, 'r', encoding='utf-8') as f:
            subtitles_readlines = f.readlines()
        clean_subtitles = []
        for line in subtitles_readlines:
            if "-->" not in line and not line.strip().isdigit():
                clean_subtitles.append(line.strip())
        subtitles_text = "\n".join(clean_subtitles)
        collection = init_milvus()
        store_embeddings_in_milvus(collection, file_path, subtitles_text)
        insert_video_info(url, file_path, video_title, subtitles)
        st.success(f"视频 '{video_title}' 下载完成，路径: {file_path}")


def audio_Download(url, output_dir):
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
        info_dict = ydl.extract_info(url, download=True)  # 下载视频信息
        video_title = info_dict.get('title', None)
        video_extension = info_dict.get('ext', None)
        file_path = os.path.join(output_dir, f"{video_title}.mp3")
        subtitle_file = doubao_api_ch.convert_video_to_srt(file_path)[1]  # 0-代表中文原版字幕文件，1-代表中英双语字幕文件
        if os.path.exists(subtitle_file):
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                subtitles = f.read()
        # 将视频信息存储到数据库中

        with open(subtitle_file, 'r', encoding='utf-8') as f:
            subtitles_readlines = f.readlines()
        clean_subtitles = []
        for line in subtitles_readlines:
            if "-->" not in line and not line.strip().isdigit():
                clean_subtitles.append(line.strip())
        subtitles_text = "\n".join(clean_subtitles)
        collection = init_milvus()
        store_embeddings_in_milvus(collection, file_path, subtitles_text)
        insert_video_info(url, file_path, video_title, subtitles)
        st.success(f"视频 '{video_title}' 下载完成，路径: {file_path}")


# 连接到Milvus
def init_milvus():
    default_server.start()
    connections.connect(host="localhost", port="19530")  # faiss_embedding维度为2560
    # 定义collection的schema,(id,file_path,subtitles,embeddings)
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="file_path", dtype=DataType.VARCHAR, max_length=3000),
        FieldSchema(name="subtitles", dtype=DataType.VARCHAR, max_length=50000),
        FieldSchema(name="embeddings", dtype=DataType.FLOAT_VECTOR, dim=2560)
    ]
    schema = CollectionSchema(fields, description="youtube视频字幕embedding存储")
    # 如果 collection 已经存在，直接加载
    if utility.has_collection("video_subtitles_embedding"):
        collection = Collection("video_subtitles_embedding")
    else:
        # 如果不存在则创建新的
        collection = Collection("video_subtitles_embedding", schema=schema)
    # 创建索引
    collection.create_index(field_name="embeddings",
                            index_params={"index_type": "IVF_FLAT", "metric_type": "L2", "params": {"nlist": 128}})
    return collection


# 将字幕生成嵌入，并存入 Milvus
def store_embeddings_in_milvus(collection, video_path, subtitles):
    # 获取embeddings
    embeddings = faiss_openai.faiss_embeddings(subtitles)
    data = [
        [video_path],  # 文件路径
        [subtitles],  # 字幕文本
        [embeddings]  # 字幕嵌入向量
    ]
    collection.insert(data)
    # 保存数据到Milvus
    collection.flush()


# 播放视频
def play_video(file_path):
    st.video(file_path)


# 更新视频库
def update_video_library(output_dir):
    videos = [f for f in os.listdir(output_dir) if f.endswith(('.mp4', '.avi'))]
    return videos


# 删除视频
def delete_video(file_path):
    os.remove(file_path)


def youtube_download():
    # 用户输入
    st.header("YouTube视频下载")
    url_input = st.text_area("输入要下载的链接（使用空格键分隔多个链接）")
    download_video_option = st.checkbox("下载最佳品质的MP4视频文件")
    download_audio_option = st.checkbox("下载最佳品质的MP3音频文件")
    download_button = st.button("开始下载")
    output_dir = "downloads"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if download_button:
        if not download_audio_option and not download_video_option:
            st.error("请至少选择一个格式文件。")
        elif not url_input:
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
                        video_Download(url, output_dir)
                        st.success(f"视频下载完成：{url}")
                    except Exception as e:
                        st.error(f"视频下载失败：{url} 错误信息：{e}")
                if download_audio_option:
                    try:
                        audio_Download(url, output_dir)
                        st.success(f"音频下载完成：{url}")
                    except Exception as e:
                        st.error(f"音频下载失败：{url} 错误信息：{e}")


def video_lib():
    st.header("YouTube视频库")
    output_dir = "downloads"
    videos = update_video_library(output_dir)
    conn = sqlite3.connect("youtube_video.db")
    cursor = conn.cursor()
    if videos:
        for video in videos:
            video_path = os.path.join(output_dir, video)
            st.video(video_path)
            # 添加删除视频和查看字幕按钮
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(f"删除 {video}"):
                    delete_video(video_path)
                    cursor.execute("DELETE FROM videos WHERE file_path = ?", (video_path,))
                    conn.commit()  # 提交事务
                    st.warning(f"{video} 已删除。")
            with col2:
                if st.button(f"查看字幕 {video}"):
                    cursor.execute("SELECT subtitles FROM videos WHERE file_path = ?", (video_path,))
                    result = cursor.fetchone()
                    conn.close()
                    if result is not None and len(result) > 0:
                        subtitles_content = result[0]
                    else:
                        st.warning("没有找到字幕内容。")
                    st.text_area(f"字幕内容：{video}", subtitles_content, height=300)


def milvus():
    st.header("文本检索(相似度最高的三个视频文本）")
    text_searching = st.text_area("输入要查找的文本关键词:")
    text_searching_button = st.button("开始查找")
    if text_searching_button:
        if not text_searching:
            st.error("请输入至少一个关键词。")
        else:
            # 初始化 Milvus 并连接到 collection
            query_text = text_searching
            collection = init_milvus()
            query_response = client.embeddings.create(
                input=query_text,
                model="ep-20240825231524-74lh4",
                encoding_format="float"
            )
            # query_embedding = np.array([item.embedding for item in query_response.data])
            query_embedding = query_response.data[0].embedding
            # 执行 Milvus 搜索
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            collection.load()
            results = collection.search(data=[query_embedding], anns_field="embeddings", param=search_params, limit=3,
                                        output_fields=["file_path", "subtitles"])
            if results:
                for result in results:
                    for hit in result:
                        file_path = hit.get('file_path')
                        subtitles = hit.get('subtitles')
                        st.subheader(f"视频文件：{os.path.basename(file_path)}")
                        st.text_area(f"字幕内容:", subtitles, height=400)
                        if os.path.exists(file_path):
                            st.video(file_path)


def doubao_chatting():
    st.header("视频文本多轮对话")
    conn = sqlite3.connect("youtube_video.db")
    cursor = conn.cursor()
    cursor.execute('SELECT title FROM videos')
    video_title = [row[0] for row in cursor.fetchall()]
    conn.close()
    selected_video = st.selectbox("选择视频", video_title)
    output_dir = "downloads"
    video_path = os.path.join(output_dir, selected_video + '.mp4')

    # 初始化或更新 st.session_state 以存储选择的视频路径
    if "last_selected_video" not in st.session_state:
        st.session_state.last_selected_video = None

    conn = sqlite3.connect("youtube_video.db")
    cursor = conn.cursor()
    # 加载选中视频文件的字幕（根据video_path查找数据库）
    if selected_video:
        cursor.execute("SELECT subtitles FROM videos WHERE file_path = ?", (video_path,))
        result = cursor.fetchone()
        conn.close()

        if result is not None and len(result) > 0:
            video_content = result[0]
            text_str = video_content
        else:
            text_str = ""  # 如果没有结果，空白文本
        if st.session_state.last_selected_video != selected_video:
            # 当视频选择发生变化时，重新初始化对话
            st.session_state.messages = []
            st.session_state.messages.append({"role": "system",
                                              "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手。我将输入一些音频和视频内容作为我们对话的基础：" + text_str})
            # 更新选中的视频路径
            st.session_state.last_selected_video = selected_video
    # 初始化对话system信息
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages = [{"role": "system",
                                      "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手。我将输入一些音频和视频内容作为我们对话的基础：" + text_str}]
    # 显示对话历史
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        elif message["role"] == "assistant":
            with st.chat_message("assistant"):
                st.write(message["content"])
    # 用户输入对话内容
    user_input = st.text_input("请输入对话内容：")
    # 发送消息并调用模型生成新对话
    if st.button("发送") and user_input:
        # 把用户输入添加到对话历史中
        st.session_state.messages.append({"role": "user", "content": user_input})
        # 调用模型生成新对话，并更新对话历史
        response = doubao_chatting_single_stream.doubao_streaming(user_input, st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": response})
        # 显示新生成的消息
        with st.chat_message("user"):
            st.write(user_input)
        with st.chat_message("assistant"):
            st.write(response)


page_names_to_funcs = {
    "—": intro,
    "YouTube视频下载": youtube_download,
    "YouTube视频库": video_lib,
    "音视频字幕文本检索": milvus,git init
    "音视频字幕多轮对话": doubao_chatting
}

demo_name = st.sidebar.selectbox("Choose a demo", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()
# streamlit run streamlit_app.py
