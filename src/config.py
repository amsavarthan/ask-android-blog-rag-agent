import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import OllamaEmbeddings

load_dotenv()

ALLOW_REFRESH = False

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

OLLAMA_EMBEDDING_MODEL = "mxbai-embed-large"     
OLLAMA_LLM_MODEL_NAME = "llama3.1"

BLOG_URL = "https://android-developers.googleblog.com/"
PAGES_TO_SCRAPE = 5

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

BUILD_DIR = "context"
POSTS_PICKLE = f"{BUILD_DIR}/blog_posts.pkl"
VECTOR_STORE_DIR = f"{BUILD_DIR}/faiss_index"

def get_llm(api_key):
    if not api_key:
        raise ValueError("Google API key is not set.")
    if not api_key.startswith("AIza"):
        raise ValueError("Invalid Google API key.")
    
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.5,
        api_key=api_key
    )

embedding_model = OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL)