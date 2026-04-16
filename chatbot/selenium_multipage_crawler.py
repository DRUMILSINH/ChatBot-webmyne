# --- For HTML to markdown -----
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import html2text
import time
import requests

# visited_urls = set()

def is_allowed_by_robots(url, user_agent='*'):
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = f"{base_url}/robots.txt"

    rp = RobotFileParser()
    rp.set_url(robots_url)

    try:
        rp.read()
        return rp.can_fetch(user_agent, url)
    except:
        # Default to allow if robots.txt can't be fetched
        return True

def extract_links(soup, base_url):
    links = set()
    for tag in soup.find_all("a", href=True):
        href = tag['href']
        absolute_url = urljoin(base_url, href)
        if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
            links.add(absolute_url.split("#")[0])  # remove anchor fragments
    return links

#########
def normalize_to_official_domain(url, official_base="https://www.webmyne.com"):
    parsed_url = urlparse(url)
    if parsed_url.netloc.startswith("192.168.") or parsed_url.netloc.startswith("localhost"):
        return url.replace(f"{parsed_url.scheme}://{parsed_url.netloc}", official_base)
    return url
#####

def convert_html_to_markdown(html, base_url=""):
    converter = html2text.HTML2Text()
    converter.images_to_alt = True
    converter.body_width = 0
    converter.single_line_break = True
    # markdown = converter.handle(html)
    # return markdown
    if base_url:##########
        converter.baseurl = base_url  # Ensures relative links are made absolute
    return converter.handle(html) ########

def is_url_live(url, timeout=10):
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False

def get_markdown_and_links_from_page(url):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)
        time.sleep(8)  # allow JS to load

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        html = str(soup)

        markdown_text = convert_html_to_markdown(html,url) ###

        page_title = soup.title.string.strip() if soup.title else "Untitled"
        meta_description = soup.find("meta", attrs={"name": "description"})
        description = meta_description["content"] if meta_description and 'content' in meta_description.attrs else page_title
        links = extract_links(soup, url)

        return markdown_text, {
            'title': page_title,
            'url': normalize_to_official_domain(url), ###
            'description': description
        }, links

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return "", {}, set()
    finally:
        driver.quit()

def crawl_website(start_url, max_pages=None, seen_urls=None):
    if seen_urls is None:
        seen_urls = set()

    visited_urls = set(seen_urls)
    to_visit = [start_url]
    all_results = []
    all_found_links = set()
    while to_visit and len(visited_urls) < max_pages:

        url = to_visit.pop(0)

        if url in visited_urls or url in seen_urls:
            continue

        if not is_allowed_by_robots(url):
            print(f"Blocked by robots.txt: {url}")
            visited_urls.add(url)
            continue

        if not is_url_live(url):
            print(f"Skipped dead/broken URL: {url}")
            visited_urls.add(url)
            continue

        print(f"Crawling: {url}")


        markdown, metadata, found_links = get_markdown_and_links_from_page(url)
        print(f"Found {len(found_links)} links on {url}")

        if markdown:
            all_results.append({'text': markdown, 'metadata': metadata})
        visited_urls.add(url)
        all_found_links.update(found_links)

        for link in found_links:
            normalized_link = normalize_to_official_domain(link) ####
            # print(f"Found links: {link}")
            # if link not in visited_urls and link not in seen_urls and link not in to_visit:
            #     to_visit.append(link)
            print(f"Found link: {normalized_link}")
            if normalized_link not in visited_urls and normalized_link not in seen_urls and normalized_link not in to_visit:
                to_visit.append(normalized_link)

    return all_results, visited_urls, all_found_links

