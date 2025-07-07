#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, parse_qs

rank_list_url = "https://finance.naver.com/news/news_list.naver?mode=RANK"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}


def get_pages_info(url):
    # rank_list_url = "https://finance.naver.com/news/news_list.naver?mode=RANK"
    # TEST: print(f"page_url: {get_pages_info(rank_list_url)}")
    response = requests.get(url, headers=headers)
    response.encoding = "euc-kr"
    html = BeautifulSoup(response.text, "lxml")
    pgrr = html.find("td", class_="pgRR")
    s = str(pgrr.a["href"]).split('=')
    lastpage = s[-1]
    return ['{}&page={}'.format(url, page) for page in range(1, int(lastpage) + 1)]

def get_article_url(page_url):
    # rank_list_url = "https://finance.naver.com/news/news_list.naver?mode=RANK"
    # TEST: print(f"article_url: {get_article_url(rank_list_url)}")
    response = requests.get(page_url, headers=headers)
    response.encoding = "euc-kr"
    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    for item in soup.select("ul.newsList li"):
        a_tag = item.find("a")
        href = a_tag.get("href")
        if href.startswith("https://"):
            links.append(href)
        else:
            parsed = urlparse(href)
            query = parse_qs(parsed.query)
            article_id = query.get("article_id", [""])[0]
            office_id = query.get("office_id", [""])[0]
            full_url = f"https://n.news.naver.com/mnews/article/{office_id}/{article_id}"
            links.append(full_url)
    return (links)

def clean_filename(s):
    # 파일명에 사용할 수 없는 문자 제거
    return re.sub(r'[\\/:*?"<>|]', '_', s)

def get_article_content(article_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(article_url, headers=headers)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    title_area = soup.find("h2", id="title_area")
    if title_area:
        paragraphs = title_area.find_all("p")
        if paragraphs:
            title = "\n".join(p.get_text(strip=True) for p in paragraphs)
        else:
            title = title_area.get_text(strip=True)
    date_time_tag = soup.find(attrs={"data-date-time": True})
    if date_time_tag:
        date_time_value = date_time_tag["data-date-time"]
        print("data-date-time 값:", date_time_value)
    else:
        print("data-date-time 속성을 찾을 수 없습니다.")
    print(f"article_url:{article_url}")
    match = re.search(r"/article/(\d{3})/(\d+)", article_url)
    if match:
        office_id = match.group(1)
        article_id = match.group(2)
        print("office_id:", office_id)
        print("article_id:", article_id)
    else:
        print("해당 형식의 URL이 아닙니다.")
    title=f"{date_time_value.replace('-', '').replace(':', '').replace(' ', '-')}_{office_id}_{article_id}_{title}"

    content_area = soup.find("article", id="dic_area")
    if content_area:
        paragraphs = content_area.find_all("p")
        if paragraphs:
            content = "\n".join(p.get_text(strip=True) for p in paragraphs)
        else:
            content = content_area.get_text(strip=True)
        return title, content
    else:
        article_body = soup.find("div", class_="article_body")
        if article_body:
            return title, article_body.get_text(strip=True)
    return ""


for page in get_pages_info(rank_list_url):
    for article_url in get_article_url(page):
        title, content = get_article_content(article_url)
        filename = clean_filename(title)
        with open("data/"+filename+".txt", "w", encoding="utf-8") as f:
            f.write(content)
        print(f"기사 본문이 '{filename}' 파일로 저장되었습니다.")