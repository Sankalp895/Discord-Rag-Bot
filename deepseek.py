from openai import OpenAI
import os
from dotenv import load_dotenv
import faiss
import numpy as np


load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
DEEPSEEK_DEPLOYMENT = "DeepSeek-R1"

#initializing
client = OpenAI(
    base_url=AZURE_ENDPOINT,
    api_key=AZURE_API_KEY
)
def ask_deepseek(question, context=""):
    completion = client.chat.completions.create(
        model=DEEPSEEK_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "You are an FAQ assistant."},
            {"role": "user", "content": f"Question: {question}\nContext: {context}"}
        ]
    )
    return completion.choices[0].message.content

# FAIS
def build_faiss_index(embeddings: np.ndarray):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)  # L2 distance
    index.add(embeddings)
    return index

def search_index(index, query_vector, k=3):
    distances, indices = index.search(query_vector, k)
    return distances, indices
