import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def get_data_from_website(url):
    """
    Retrieve plain text content and metadata from a given URL.

    Args:
        url (str): The URL to fetch content from.

    Returns:
        tuple: (cleaned plain text content, metadata dictionary)
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch URL: {url}\nError: {e}")
        return None, None

    soup = BeautifulSoup(response.content, 'html.parser')

    # Remove unwanted scripts and styles
    for script in soup(["script", "style", "noscript"]):
        script.decompose()

    # Extract clean plain text
    text = soup.get_text(separator='\n', strip=True)

    # Extract metadata
    parsed_url = urlparse(url)
    try:
        page_title = soup.title.string.strip()
    except:
        page_title = parsed_url.path.strip("/").replace("/", "-") or "Untitled"

    meta_description_tag = soup.find("meta", attrs={"name": "description"})
    meta_keywords_tag = soup.find("meta", attrs={"name": "keywords"})

    description = meta_description_tag.get("content", "").strip() if meta_description_tag else page_title
    keywords = meta_keywords_tag.get("content", "").strip() if meta_keywords_tag else ""

    metadata = {
        "title": page_title,
        "url": url,
        "description": description,
        "keywords": keywords
    }

    return text, metadata

if __name__ == "__main__":
    test_url = "https://www.webmyne.com/"
    text, metadata = get_data_from_website(test_url)

    if text:
        print("\n--- Extracted Text (First 15000 chars) ---\n")
        print(text[:15000] + "\n...")

        print("\n--- Metadata ---\n")
        print(metadata)
    else:
        print("No data was extracted.")


# import requests
# from bs4 import BeautifulSoup
# import html2text
#
#
# def get_data_from_website(url):
#     """
#     Retrieve text content and metadata from a given URL.
#
#     Args:
#         url (str): The URL to fetch content from.
#
#     Returns:
#         tuple: A tuple containing the text content (str) and metadata (dict).
#     """
#     # Get response from the server
#     response = requests.get(url)
#     if response.status_code == 500:
#         print("Server error")
#         return
#     # Parse the HTML content using BeautifulSoup
#     soup = BeautifulSoup(response.content, 'html.parser')
#
#     # # Removing js and css code
#     # for script in soup(["script", "style"]):
#     #     script.extract()
#
#     # Extract text in markdown format
#     html = str(soup)
#     html2text_instance = html2text.HTML2Text()
#     html2text_instance.images_to_alt = True
#     html2text_instance.body_width = 0
#     html2text_instance.single_line_break = True
#     text = html2text_instance.handle(html)
#
#     # Extract page metadata
#     try:
#         page_title = soup.title.string.strip()
#     except:
#         page_title = url.path[1:].replace("/", "-")
#     meta_description = soup.find("meta", attrs={"name": "description"})
#     meta_keywords = soup.find("meta", attrs={"name": "keywords"})
#     if meta_description:
#         description = meta_description.get("content")
#     else:
#         description = page_title
#     if meta_keywords:
#         meta_keywords = meta_description.get("content")
#     else:
#         meta_keywords = ""
#
#     metadata = {'title': page_title,
#                 'url': url,
#                 'description': description,
#                 'keywords': meta_keywords}
#
#     return text, metadata
#
# if __name__ == "__main__":
#     url = "https://www.webmyne.com/"
#     text, metadata = get_data_from_website(url)
#
#     print("\n--- Extracted Text ---\n")
#     print(text[:5000] + "\n...")
#
#     print("\n--- Metadata ---\n")
#     print(metadata)