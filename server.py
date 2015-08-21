import muffin
import asyncio
import aiohttp
from fn.monad import Option
from bs4 import BeautifulSoup
from operator import setitem
import json


@asyncio.coroutine
def handle_laf_scraping(url, isbn):
    @asyncio.coroutine
    def exctract_metadata(text, isbn, container=dict()):
        soup = BeautifulSoup(response_txt, "html.parser")
        Option(soup.find("span", {"itemprop": "name"}))\
            .map(lambda item: item.text)\
            .map(lambda item: setitem(container, "title", item))\
            .get_or(None)

        Option(soup.find("div", {"class": "head-intro"}))\
            .map(lambda item: item.find("h2"))\
            .map(lambda item: item.find("a"))\
            .map(lambda item: item.text)\
            .map(lambda item: setitem(container, "authors", item))\
            .get_or(None)

        Option(soup.find("div", {"id": "detail-content"}))\
            .map(lambda item: item.find("div", {"class": "block-content"}))\
            .map(lambda item: item.find("p"))\
            .map(lambda item: item.text)\
            .map(lambda item: setitem(container, "description", item))\
            .get_or(None)

        Option(soup.find("img", {"itemprop": "image"}))\
            .map(lambda item: "http:" + item["src"])\
            .map(lambda item: setitem(container, "imageLinks", item))\
            .get_or(None)

        Option(soup.find("div", {"id": "block-more-info"}))\
            .map(lambda item: item.find("ul"))\
            .map(lambda item: item.find("li"))\
            .map(lambda item: item.find("div"))\
            .map(lambda item: item.find("a"))\
            .map(lambda item: setitem(container, "tags", item.text))\
            .get_or(None)

        container["industryIdentifiers"] = isbn
        container["source"] = "LAF"
        print(container)
        return container
    response_txt = yield from do_request(url)
    response = yield from exctract_metadata(response_txt, isbn)
    return response


@asyncio.coroutine
def handle_amazon_scraping(url, isbn):
    @asyncio.coroutine
    def exctract_main_link(text):
        soup = BeautifulSoup(text, "html.parser")
        return soup.find("a", {"class": "s-access-detail-page"}).get("href", None)

    @asyncio.coroutine
    def exctract_metadata(text, isbn, container=dict()):
        soup = BeautifulSoup(response_txt, "html.parser")

        Option(soup.find("span", {"id": "productTitle"}))\
            .map(lambda item: item.text)\
            .map(lambda item: setitem(container, "title", item))\
            .get_or(None)

        Option(soup.find("span", {"class": "author"}))\
            .map(lambda item: item.find("a"))\
            .map(lambda item: item.text)\
            .map(lambda item: setitem(container, "authors", item))\
            .get_or(None)

        Option(soup.find("div", {"id": "bookDescription_feature_div"}))\
            .map(lambda item: item.find("noscript"))\
            .map(lambda item: item.find("div"))\
            .map(lambda item: item.text)\
            .map(lambda item: setitem(container, "description", item))\
            .get_or(None)

        Option(soup.find("div", {"id": "img-canvas"}))\
            .map(lambda item: item.find("img"))\
            .map(lambda item: item.get("data-a-dynamic-image", None))\
            .map(lambda item: item.split("\""))\
            .map(lambda item: item[1])\
            .map(lambda item: setitem(container, "imageLinks", item))\
            .get_or(None)

        container["industryIdentifiers"] = isbn
        container["source"] = "AM"
        return container
    response_txt = yield from do_request(url)
    detail_link = yield from exctract_main_link(response_txt)
    response_txt = yield from do_request(detail_link)
    response = yield from exctract_metadata(detail_link, isbn)
    return response


app = muffin.Application('amazon_scraper')


@asyncio.coroutine
def do_request(url, method="GET"):
    response = yield from aiohttp.request(method, url)
    text = yield from response.read()
    return text


@app.register('/scrape')
def index(request):
    amazon_url = "http://www.amazon.it/gp/search/search-alias=stripbooks&field-isbn="
    laf_url = "http://www.lafeltrinelli.it/libri/rfrrrfrre/rdferd/"

    flattened_qs = Option(request.query_string)\
        .map(lambda item: item.split("&"))\
        .map(lambda exqs: [(item.split("=")[0], item.split("=")[1]) for item in exqs])\
        .map(lambda item: dict(item)).get_or(dict())

    data = yield from asyncio.gather(*[asyncio.Task(handle_amazon_scraping(
        url="%s%s" % (amazon_url, flattened_qs["isbn"]),
        isbn=flattened_qs["isbn"])), asyncio.Task(handle_laf_scraping(
        url="%s%s" % (laf_url, flattened_qs["isbn"]),
        isbn=flattened_qs["isbn"]))])
    return aiohttp.web.Response(text=json.dumps(data), content_type="application/json")
