import faiss
import numpy as np
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv('environment.env')

# srt_file_path = 'chuli.srt'
# 将字幕转换为列表
# subtitles_texts = extract_subtitles_from_srt_list(srt_file_path)
# 输入文本列表
# texts = subtitles_texts

# 字幕文本的embedding
def faiss_embeddings(texts):
    # 设置 API 密钥
    client = OpenAI(
        api_key=os.getenv("API_KEY_OPENAI"),
        base_url="https://ark.cn-beijing.volces.com/api/v3",
    )
    # 调用嵌入模型 API
    resp = client.embeddings.create(
        model=os.getenv("embedding_model"),
        input=texts,
        encoding_format="float"
    )
    # 提取嵌入结果
    # embeddings = np.array([item.embedding for item in resp.data])
    embeddings = resp.data[0].embedding
    # 获取嵌入的维度
    # embedding_dim = embeddings.shape[1]
    return embeddings


# query_text的搜索
def faiss_searching(embedding_dim, embeddings, query_text, texts):
    client = OpenAI(
        api_key=os.getenv("API_KEY_OPENAI"),
        base_url="https://ark.cn-beijing.volces.com/api/v3",
    )
    # 创建一个 FAISS 索引，使用 L2（欧几里得距离）作为度量
    index = faiss.IndexFlatL2(embedding_dim)
    # 将嵌入向量添加到索引中
    index.add(embeddings)
    # 如果需要保存索引到磁盘以便后续使用
    faiss.write_index(index, "faiss_index.bin")
    # 生成查询文本的嵌入向量
    query_response = client.embeddings.create(
        input=query_text,
        model=os.getenv("embedding_model"),
        encoding_format="float"
    )
    query_embedding = np.array([item.embedding for item in query_response.data])
    # 搜索最相似的向量（返回 top 3）
    D, I = index.search(query_embedding, k=3)  # I-index,D-disatance
    search_text = ""
    for i in I[0]:
        search_text += texts[i]
    return search_text


