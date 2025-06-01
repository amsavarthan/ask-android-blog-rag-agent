# 🧠 Ask Android Blog – RAG Agent

![Screenshot](/screenshot/screenshot.jpeg "App Screenshot")

A lightweight **Retrieval-Augmented Generation (RAG)** application built with **LangChain**, designed to answer questions based on the **official Android Developers Blog**.
This project comes preloaded with content from **50 blog pages**, providing ample context to power intelligent, blog-aware responses.


## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/amsavarthan/ask-android-blog-rag-agent

cd ask-android-blog-rag-agent
```

### 2. Add your API key

Create a `.env` file and include your Google API key (required for Gemini or other LLM providers):

```env
DOCKER_HOST_PORT=
GOOGLE_API_KEY=
```

### 3. Start the app with Docker

Ensure you have Docker and Docker Compose installed. Then run:

```bash
docker-compose up -d
```

Visit the app at [http://localhost:8000](http://localhost:8000)

> 💡 **Note**
> The app comes with **50 pages of pre-scraped blog content**. You can ask questions related to the topics covered in those posts.


## 🛠️ Customization

### 🔄 Switching to Ollama or Other LLMs

To use **Ollama** or another LLM instead of Gemini, open `config.py` and modify the `get_llm()` function accordingly.
You can also change the **embedding model** from the same file.


### ♻️ Enable Blog Refresh in the UI

To allow dynamic blog updates from the sidebar, set `ALLOW_REFRESH = True` in `config.py`.

> ⚠️ **Important:**
> Use caution when setting a high number of pages to scrape. Excessive requests may put unnecessary load on the Android Developers Blog.

## 📂 Project Structure

```
├── src/                  
├───── app.py               # Streamlit frontend
├───── config.py            # App Configuration
├── context/                # Preloaded vector store
├── .env                    # Environment variables
├── docker-compose.yml      # Container config
└── requirements.txt        # Python dependencies
```


## 📬 Feedback

If you encounter bugs or have feature suggestions, feel free to open an issue or submit a pull request.


## 📖 License

This project is open source under the [MIT License](LICENSE).