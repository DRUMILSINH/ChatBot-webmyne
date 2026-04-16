from chatbot.utils import make_local_chain, store_docs


def retrieve_answer(vector_id: str, query: str) -> dict:
    """
    Query the vector database identified by vector_id.
    Returns a dictionary with the result and source metadata.
    """
    try:
        chain = make_local_chain(vector_id)
        result = chain.invoke({"query": query, "context": ""})

        sources = []
        for i, doc in enumerate(result.get("source_documents", []), 1):
            meta = doc.metadata
            sources.append({
                "chunk_number": i,
                "url": meta.get("url", "N/A"),
                "chunk_id": meta.get("chunk_id", "N/A"),
                "page_id": meta.get("source", "N/A"),
                "md5": meta.get("md5", "N/A"),
                "content": doc.page_content.strip()[:800]
            })

        return {
            "answer": result["result"],
            "sources": sources
        }

    except Exception as e:
        return {
            "error": str(e)
        }


def crawl_and_embed(url: str, vector_id: str, max_pages: int = 1, embed: bool = True, base_url: str = None) -> dict:
    """
    Crawls and embeds a site for a given company (vector_id).
    Returns status and logs useful for debugging.
    """
    try:
        store_docs(
            url=url,
            vector_id=vector_id,
            max_pages=max_pages,
            embed=embed
        )
        return {
            "status": "success",
            "message": f"Website crawled and embedded successfully for vector_id: {vector_id}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

