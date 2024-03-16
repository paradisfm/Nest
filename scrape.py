import os
import logging
import json
import requests
from urllib import request
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from pydotmap import DotMap

furniture_styles = ["art deco", "boho", "coastal", "colonial", "farmhouse", "midcentury modern", "minimalist", "modern", "retro", "rustic", "scandinavian", "traditional"]
furnitures = ["bedframe", "chair", "coffee_tables", "desks", "dining_tables", "dressers", "lamps", "nightstand", "ottoman", "shelves", "sofas"]

class PinterestImageScraper:
    def __init__(self):
        self.downloaded_images = set()

    # Search Google for given keyword on Pinterest
    def search_urls(self, max_images, key):
        keyword = key.replace(" ", "+") + " pinterest"
        query = f'https://www.google.com/search?hl=en&q={keyword}'
        res = requests.get(query)
        urls = self.get_base_urls(res.content, max_images)
        logging.debug('searching urls...')
        return urls
     
    # Parse search results for Pinterest pin URLs
    def get_base_urls(self, body, max_images):
        url_list = []
        html = BeautifulSoup(body, 'html.parser')
        links = html.select('a[href^="/url?q=https://www.pinterest."]')
        for link in links:
            href = link.get('href')
            parsed = urlparse(href)
            qs = parse_qs(parsed.query)
            if 'q' in qs:
                url = qs['q'][0]
                if 'pinterest.' in url:
                    url_list.append(url)
                    if len(url_list) == max_images:
                        break
        logging.debug('base urls retrieved...')
        return url_list

    # Take image URL from pin data
    def get_image_url(self, max_images, key, piece, style):
        url_list = self.search_urls(max_images, f"{style} {piece}")
        image_urls = []

        for url in url_list:
            resp = requests.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'html.parser')
                data_soup = soup.find_all("script", attrs={"id": "__PWS_DATA__"})
                data_indiv = [a.text for a in data_soup]
                json_data = json.dumps(data_indiv)
                json_data = json.loads(json_data)

                for a in json_data:
                    data = DotMap(json.loads(a))

                    for pin in data.props.initialReduxState.pins:
                        if isinstance(data.props.initialReduxState.pins[pin].images.get("orig"), list):
                            for i in data.props.initialReduxState.pins[pin].images.get("orig"):
                                image_url = i.get("url")
                                if image_url:
                                    image_urls.append(image_url)
                        else:
                            image_url = data.props.initialReduxState.pins[pin].images.get("orig").get("url")
                            if image_url:
                                image_urls.append(image_url)
        logging.debug('image urls extracted...')

        # Filter out None values
        image_urls = [url for url in image_urls if url is not None]

        if len(image_urls) >= max_images:
            return image_urls[:max_images]
        else:
            return image_urls

    # Retrieve & download images
    def scrape(self, key, max_images):
        for piece in furnitures:
            for style in furniture_styles:
                urls = self.get_image_url(max_images, key, piece, style)
                for url in urls:
                    self.download_image(url, piece, style)
    
    def download_image(self, url, piece, style):
        fpath = rf'data/{piece}/{style}'
        if not os.path.exists(fpath):
            os.makedirs(fpath)
        try:
            fname = os.path.join(fpath, os.path.basename(url))
            if not os.path.exists(fname):
                request.urlretrieve(url, fname)
                logging.debug(f'Downloaded {url} to {fname}')
            else:
                logging.debug(f'File already exists: {fname}')
        except Exception as e:
            logging.error(f'Error downloading {url}: {e}')
   
if __name__ == "__main__":
   scraper = PinterestImageScraper()
   logging.basicConfig(level=logging.DEBUG)
   for piece in furnitures:
       for style in furniture_styles:
           scraper.scrape(key=f"{style} {piece}", max_images=300)
