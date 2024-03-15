import os
import re
import json
import requests
from urllib import request
from bs4 import BeautifulSoup as soup
from pydotmap import DotMap

furniture_styles = ["art deco", "asian", "boho", "coastal", "colonial", "farmhouse", "midcentury modern", "minimalist", "modern", "retro", "rustic", "scandinavian", "traditional"]
furnitures = ["bedframe", "chair", "coffee_tables", "desks", "dining_tables", "dressers", "lamps", "nightstand", "ottoman", "shelves", "sofas"]

class PinterestImageScraper:

    def get_pinterest_links(body, max_images):
        searched_urls = []
        html = soup(body, 'html.parser')
        links = html.select('#main > div > div > div > a')
        for link in links:
            link = link.get('href')
            link = link.replace('/url?q=', '')
            if link.startswith('https://www.pinterest'):
                if link not in searched_urls:
                    searched_urls.append(link)
                    if len(searched_urls) == max_images:
                        return searched_urls
                    
        return searched_urls

    def save_image_url(self, max_images, pin_data):
        url_list = []
        for js in pin_data:
            data = DotMap(json.loads(js))
            urls = []
            for pin in data.props.initialReduxState.pins:
                if isinstance(data.props.initialReduxState.pins[pin].images.get("orig"), list):
                    for i in data.props.initialReduxState.pins[pin].images.get("orig"):
                        urls.append(i.get("url"))
                else:
                    urls.append(data.props.initialReduxState.pins[pin].images.get("orig").get("url"))
                for url in urls:
                    if url not in url_list:
                        if len(url_list) <= max_images:
                            url_list.append(url)
        return url_list
    
    def extract_urls(self, max_images, key):
        keyword = key + " pinterest"
        keyword = keyword.replace(" ", "+")
        url = f'https://www.google.com/search?hl=en&q={keyword}'
        res = requests.get(url)
        extracted_urls = self.get_pinterest_links(res.content, max_images)
        return extracted_urls

    def scrape(self, key, max_images):
        extracted_urls = self.start_scraping(max_images, key)
        url_list = []
        data_list = []
        for url in extracted_urls:
            res = requests.get(url)
            html = soup(res.text, 'html.parser')
            json_data = html.find_all("script", attrs={"id": "__PWS_DATA__"})
            for a in json_data:
                data_list.append(a.string)
        self.download_images(url_list, max_images)

    def download_images(self, urls):
        for url in urls:
            for piece in furnitures:
                for style in furniture_styles:
                    fpath = rf'data/{piece}/{style}'
                    if not os.path.exists(fpath):
                        os.makedirs(fpath)
                    try:
                        fname = os.path.join(fpath, url[40:])
                        request.urlretrieve(url, fname)
                        print(f'Downloaded {url} to {fname}')
                    except Exception as e:
                        print(f'Error downloading {url}: {e}')
    

if __name__ == "__main__":
    scraper = PinterestImageScraper()
    for piece in furnitures:
        for style in furniture_styles:
            scraper.scrape(key=f"{style} {piece}", max_images=300)
