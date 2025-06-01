import os
import pickle
import shutil
import requests
import streamlit as st
from bs4 import BeautifulSoup
import time

from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains.qa_with_sources.retrieval import RetrievalQAWithSourcesChain
import config


def get_blog_links(max_pages=config.PAGES_TO_SCRAPE, progress_callback=None):
    os.makedirs(config.BUILD_DIR, exist_ok=True)

    if os.path.exists(config.POSTS_PICKLE):
        with open(config.POSTS_PICKLE, "rb") as f:
            return pickle.load(f)

    urls = []
    next_page = config.BLOG_URL
    pages_scraped = 0

    while next_page and pages_scraped < max_pages:
        if progress_callback:
            progress_callback(f"Scraping page {pages_scraped+1} of {max_pages}...")

        soup = BeautifulSoup(requests.get(next_page).text, "html.parser")
        cards = soup.select(".adb-card")
        for card in cards:
            a_tag = card.select_one(".adb-card__href")
            if a_tag and (href := a_tag.get("href")):
                urls.append(href)
        next_btn = soup.select_one(".blog-pager-older-link.page-button")
        next_page = next_btn.get("href") if next_btn else None
        pages_scraped += 1
        time.sleep(0.5)  # small delay to simulate work / be polite to server

    with open(config.POSTS_PICKLE, "wb") as f:
        pickle.dump(urls, f)

    return urls


def create_vector_store(urls, progress_callback=None):
    if progress_callback:
        progress_callback("Loading and parsing blog posts...")
    loader = UnstructuredURLLoader(urls=urls)
    documents = loader.load()

    if progress_callback:
        progress_callback("Splitting documents into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP)
    chunks = splitter.split_documents(documents)

    if progress_callback:
        progress_callback("Creating embeddings...")
    embeddings = config.embedding_model

    if progress_callback:
        progress_callback("Building FAISS vector store...")
    vectorstore = FAISS.from_documents(chunks, embedding=embeddings)
    vectorstore.save_local(config.VECTOR_STORE_DIR)
    return vectorstore


def load_vector_store(progress_callback=None):
    os.makedirs(config.BUILD_DIR, exist_ok=True)

    if os.path.exists(config.VECTOR_STORE_DIR):
        if progress_callback:
            progress_callback("Loading vector store from disk...")
        embeddings = config.embedding_model
        return FAISS.load_local(config.VECTOR_STORE_DIR, embeddings, allow_dangerous_deserialization=True)
    else:
        urls = get_blog_links(progress_callback=progress_callback)
        return create_vector_store(urls, progress_callback=progress_callback)


def clear_cache_files():
    if os.path.exists(config.POSTS_PICKLE):
        os.remove(config.POSTS_PICKLE)
    if os.path.exists(config.VECTOR_STORE_DIR):
        shutil.rmtree(config.VECTOR_STORE_DIR)


def main():
    st.set_page_config(page_title="Ask Android Blog",initial_sidebar_state='collapsed')

    st.image("src/assets/android.svg", width=100)
    st.title("Ask Android Blog")
    st.markdown("Get instant answers from the official Android Developers Blog — powered by AI.")

    st.sidebar.title("Configuration")
    api_key = st.sidebar.text_input(
        "Gemini API Key:",
        type="password",
        value=config.GOOGLE_API_KEY or "",
    )

    # Determine if initial refresh is needed (no cache)
    if "refresh_in_progress" not in st.session_state:
        posts_exist = os.path.exists(config.POSTS_PICKLE)
        vectorstore_exists = os.path.exists(config.VECTOR_STORE_DIR)
        if not posts_exist or not vectorstore_exists:
            st.session_state["refresh_in_progress"] = True
            st.session_state["initial_refresh"] = True  # mark initial refresh
        else:
            st.session_state["refresh_in_progress"] = False
            st.session_state["initial_refresh"] = False

    status_placeholder = st.empty()

    # Sidebar input only shown if not initial refresh in progress
    if config.ALLOW_REFRESH and not st.session_state.get("initial_refresh", False):
        max_pages = st.sidebar.number_input(
            "Max pages to scrape:", min_value=1, value=config.PAGES_TO_SCRAPE, step=1
        )
    else:
        max_pages = config.PAGES_TO_SCRAPE  

    # Disable UI controls while refreshing
    refresh_in_progress = st.session_state.get("refresh_in_progress", False)

    if not refresh_in_progress:
        if config.ALLOW_REFRESH and st.sidebar.button("🔄 Refetch Blogs and Rebuild Vector Store"):
            st.session_state["refresh_in_progress"] = True
            status_placeholder.info("Starting refresh...")

            # Disable all widgets by rerunning with refresh_in_progress True
            st.rerun()

    # If refresh is in progress, perform it here
    if refresh_in_progress:
        progress_bar = st.progress(0)
        def progress_callback(msg):
            status_placeholder.info(msg)

        # Clear cache files
        clear_cache_files()
        progress_callback("Cleared cache files.")
        progress_bar.progress(10)

        # Scrape URLs
        urls = get_blog_links(max_pages=max_pages, progress_callback=progress_callback)
        progress_bar.progress(40)

        # Rebuild vector store
        create_vector_store(urls, progress_callback=progress_callback)
        progress_bar.progress(100)

        status_placeholder.success("Refresh complete!")
        st.session_state["refresh_in_progress"] = False
        st.session_state["initial_refresh"] = False

        # Force rerun to reset UI and enable inputs
        st.rerun()

    # Load vector store normally if no refresh
    vectorstore = load_vector_store(progress_callback=None)

    query = st.text_input("🔎 Ask a question:")

    if query:
        retriever = vectorstore.as_retriever()
        
        try:
            llm = config.get_llm(api_key=api_key)
        except ValueError as e:
            st.error(f"Error: {e}")
            return

        qa_chain = RetrievalQAWithSourcesChain.from_chain_type(
            llm=llm,
            retriever=retriever,
            return_source_documents=True,
        )

        with st.spinner("Thinking..."):
            result = qa_chain.invoke({"question": query})
            answer = result["answer"]
            sources = result.get("sources", "")

        st.subheader("💡 Answer")
        st.write(answer)

        if sources:
            st.subheader("🔗 Sources")
            for src in sources.split(","):
                st.markdown(f"- [📖 {src.strip()}]({src.strip()})")


if __name__ == "__main__":
    main()