import pysrt


def extract_subtitles_from_srt_list(srt_file_path):
    # 读取 SRT 文件

    subs = pysrt.open(srt_file_path, encoding='utf-8')
    # 提取字幕文本并存储到列表中
    subtitles_texts = [sub.text for sub in subs]
    return subtitles_texts


def extract_subtitles_from_srt_text(srt_file_path):
    # 读取 SRT 文件

    subs = pysrt.open(srt_file_path, encoding='utf-8')
    # 提取字幕文本并存储到列表中
    subtitles_texts = extract_subtitles_from_srt_list(srt_file_path)
    text_str = '\n'.join(subtitles_texts)
    return text_str

