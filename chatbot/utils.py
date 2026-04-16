import os
import json
import threading
from hashlib import md5

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA

from chatbot.text_to_doc import get_doc_chunks
from chatbot.selenium_multipage_crawler import crawl_website
from chatbot.prompt import get_prompt

try:
    from chat.security import validate_crawl_url
except Exception:  # pragma: no cover
    validate_crawl_url = None

_cache_lock = threading.Lock()
_embedding_function = None
_vector_store_cache: dict[str, Chroma] = {}


def get_vector_store(vector_id: str):
    """
    Returns a Chroma vector store for a given customer (vector_id).
    """
    global _embedding_function
    with _cache_lock:
        if _embedding_function is None:
            _embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        cached = _vector_store_cache.get(vector_id)
        if cached is not None:
            return cached

        store = Chroma(
            collection_name=vector_id,
            embedding_function=_embedding_function,
            persist_directory=f"db/{vector_id}"
        )
        _vector_store_cache[vector_id] = store
        return store

def store_docs(url: str, vector_id: str, max_pages: int = None, use_cache: bool = True, embed: bool = True):
    """
    Crawls a website and stores content into a Chroma vector DB specific to vector_id.
    """
    if validate_crawl_url:
        validate_crawl_url(url, vector_id)

    cache_file = f"db/{vector_id}/crawled_data.json"
    seen_path = f"db/{vector_id}/seen_urls.json"
    found_path = f"db/{vector_id}/found_urls.json"
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)

    pages = []
    seen_urls = set()

    if use_cache and os.path.exists(cache_file):
        print("[] Loading cached crawl data...")
        with open(cache_file, "r", encoding="utf-8") as f:
            pages = json.load(f)
            seen_urls = set(page.get("metadata", {}).get("url") for page in pages)
    else:
        print("[] No cache found. Starting fresh.")

    print(f"[] Crawling upto {max_pages} pages...")

    new_pages, visited_urls, all_found_links = crawl_website(url, max_pages=max_pages)####

    filtered_pages = [p for p in new_pages if p.get("metadata", {}).get("url") not in seen_urls]
    pages.extend(filtered_pages)

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)

    print(f"[] Already seen URLs: {len(seen_urls)}")
    print(f"[] New unique pages to embed: {len(filtered_pages)}")

    # Save seen and found URLs to disk
    with open(seen_path, "w", encoding="utf-8") as f:
        # json.dump(sorted(list(visited_urls)), f, indent=2)
        json.dump(sorted(list(seen_urls)), f, indent=2)
    with open(found_path, "w", encoding="utf-8") as f:
        json.dump(sorted(list(all_found_links)), f, indent=2)

    if not embed:
        print("[] Skipping embedding step.")
        return

    vector_store = get_vector_store(vector_id)
    existing_docs = set(doc.metadata.get("md5") for doc in vector_store.similarity_search("", k=1000))

    all_docs = []
    for page in pages:
        page_url = page.get("metadata", {}).get("url")
        text = page.get("markdown") or page.get("text", "").strip()
        metadata = page.get("metadata", {})

        if text:
            chunks = get_doc_chunks(text, metadata)
            for i, chunk in enumerate(chunks):

                chunk.metadata["source"] = page_url
                chunk.metadata["chunk_id"] = f"{page_url}_chunk_{i}"
                chunk.metadata["url"] = page_url # for correct url in UI
                chunk_hash = md5(chunk.page_content.encode("utf-8")).hexdigest()
                chunk.metadata["md5"] = chunk_hash
                if chunk_hash not in existing_docs:
                    all_docs.append(chunk)
                else:
                    print(f"[[️] Skipping duplicate chunk from {page_url} (chunk {i})")
        else:
            print(f"[] Skipping empty page: {page_url}")

    if all_docs:
        print(f"[] Storing {len(all_docs)} new chunks into ChromaDB...")
        vector_store.add_documents(all_docs )
        vector_store.persist()
        print(f"[] Stored {len(all_docs)} chunks.")
    else:
        print("[] No new chunks to embed.")

    #  Print the total number of documents now in ChromaDB
    total_chunks = vector_store._collection.count()
    print(f"[] Total chunks in ChromaDB (vector_id='{vector_id}'): {total_chunks}")

def make_local_chain(vector_id: str):
    """
    Loads the vector DB and sets up the QA retrieval chain for that customer.
    """
    print(f"[] Loading ChromaDB for vector ID: {vector_id}")
    vector_store = get_vector_store(vector_id)

    print(f"[] ChromaDB has {vector_store._collection.count()} documents.")

    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 10})
    prompt = get_prompt()
    model_name = os.getenv("OLLAMA_MODEL", "mistral")
    base_url = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))
    ollama_kwargs = {"model": model_name, "temperature": 0.0}
    if base_url:
        ollama_kwargs["base_url"] = base_url
    try:
        llm = Ollama(**ollama_kwargs)
    except TypeError:
        ollama_kwargs.pop("base_url", None)
        llm = Ollama(**ollama_kwargs)

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )
    return chain


def get_relevant_chunks(vector_id: str, query: str, k: int = 10):
    """
    Returns top-k relevant chunks from a vector DB for debugging or UI display.
    """
    vector_store = get_vector_store(vector_id)
    results = vector_store.similarity_search(query, k=k)
    return results


