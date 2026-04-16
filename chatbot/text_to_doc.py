import re
from langchain.text_splitter import MarkdownTextSplitter, RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from hashlib import md5
import hashlib


# Data Cleaning functions

def merge_hyphenated_words(text):
    return re.sub(r"(\w)-\n(\w)", r"\1\2", text)


def fix_newlines(text):
    return re.sub(r"(?<!\n)\n(?!\n)", " ", text)


def remove_multiple_newlines(text):
    return re.sub(r"\n{2,}", "\n", text)


def clean_text(text):
    """
    Cleans the text by passing it through a list of cleaning functions.

    Args:
        text (str): Text to be cleaned

    Returns:
        str: Cleaned text
    """
    cleaning_functions = [merge_hyphenated_words, fix_newlines, remove_multiple_newlines]
    for cleaning_function in cleaning_functions:
        text = cleaning_function(text)
    return text



def is_probable_heading(line):
    """
    Check if a line is likely a section header based on various formats.
    """
    stripped = line.strip()
    return (
        stripped.startswith("\n##") or
        stripped.startswith("*###") or
        stripped.startswith("\n####") or
        stripped.startswith("\n") or
        stripped.startswith("\n**   ") or
        stripped.isupper() and len(stripped.split()) <= 8
    )

def prepend_section_headers(text):
    """
    Prepend last known headers to each paragraph for better context retention.
    """
    headers = []
    lines = text.split('\n')
    final_lines = []

    for line in lines:
        stripped = line.strip()

        if is_probable_heading(stripped):
            headers.append(stripped)

        if stripped:
            # Use up to last 2 headers for better context
            context = "\n".join(headers[-2:]) if headers else ""
            final_lines.append(f"{context}\n{line}")
        else:
            final_lines.append(line)

    return "\n".join(final_lines)

def text_to_docs(text, metadata):
    """
    Converts input text to a list of Documents with metadata.

    Args:
        text (str): A string of text.
        metadata (dict): A dictionary containing the metadata.

    Returns:
        List[Document]: List of documents.
    """
    doc_chunks = []
    seen_hashes = set()
    text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1400,
    chunk_overlap=300,
    separators=["\n##### ", "\n#### ","\n### ", "\n## ", "\n", ".", " "],)

    #MarkdownTextSplitter(chunk_size=500, chunk_overlap=150)
    chunks = text_splitter.split_text(text)

    current_heading = ""
    heading_pattern = re.compile(r"(#+)\s+(.*)")

    for i, chunk in enumerate(chunks):
        chunk = chunk.strip()
        if not chunk:
            continue
        # Try  to find a heading inside the chunk
        heading_match = heading_pattern.search(chunk)
        if heading_match:
            current_heading = heading_match.group(2).strip()

        # Prepend heading if available
        if current_heading:
            chunk_with_heading = f"{current_heading}\n{chunk}"
        else:
            chunk_with_heading = chunk

        chunk_hash = hashlib.md5(chunk.encode("utf-8")).hexdigest()
        if chunk_hash in seen_hashes:
            continue
        seen_hashes.add(chunk_hash)

        doc = Document(
            page_content=chunk,
            metadata={
                **metadata,
                "chunk": i,
                "chunk_hash": chunk_hash,
                # "url": page_url ###################
            }
        )
        doc_chunks.append(doc)
    return doc_chunks


def get_doc_chunks(text, metadata):
    """
    Processes the input text and metadata to generate document chunks.

    This function takes the raw text content and associated metadata, cleans the text,
    and divides it into document chunks.

    Args:
        text (str): The raw text content to be processed.
        metadata (dict): Metadata associated with the text content.

    Returns:
        List[Document]: List of documents.
    """
    text = clean_text(text)
    doc_chunks = text_to_docs(text, metadata)
    return doc_chunks
