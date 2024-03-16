import os
import logging
import json
import requests
from urllib import request
from bs4 import BeautifulSoup
from pydotmap import DotMap

furniture_styles = ["art deco", "boho", "coastal", "colonial", "farmhouse", "midcentury modern", "minimalist", "modern", "retro", "rustic", "scandinavian", "traditional"]
furnitures = ["bedframe", "chair", "coffee_tables", "desks", "dining_tables", "dressers", "lamps", "nightstand", "ottoman", "shelves", "sofas"]

class PinterestImageScraper:

    def __init__(self):
        self.downloaded_images = set()

    # search google for given keyword on pinterest
    def search_urls(self, max_images, key):
        keyword = key + " pinterest"
        keyword = keyword.replace(" ", "+")
        query = f'https://www.google.com/search?hl=en&q={keyword}'
        res = requests.get(query)
        urls = self.get_base_urls(res.content, max_images)
        logging.debug('searching urls...')
        return urls
     
    # parse search results for pinterest pin urls
    def get_base_urls(self, body, max_images):
        url_list = []
        html = BeautifulSoup(body, 'html.parser')
        links = html.select('#main > div > div > div > a')
        for link in links:
            link = link.get('href')
            link = link.replace('/url?q=', '')
            if link.startswith('https://www.pinterest'):
                if link not in url_list:
                    url_list.append(link)
        if len(url_list) == max_images:
            return url_list
                    
        logging.debug('base urls retrieved...')           
        return url_list

    # take image url from pin data
    def get_image_url(self, max_images, key, piece, style):
        url_list = self.search_urls(max_images, key)
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
                                if image_url not in self.downloaded_images:
                                    image_urls.append(image_url)
                                    self.downloaded_images.add(image_url)
                        else:
                            image_url = data.props.initialReduxState.pins[pin].images.get("orig").get("url")
                            if image_url not in self.downloaded_images:
                                image_urls.append(image_url)
                                self.downloaded_images.add(image_url)
                            if image_url is None:
                                continue
                            logging.debug(f'image url {image_url} extracted...')
        if len(image_urls) >= max_images:
            return image_urls

    # retrieve & download images
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
            fname = os.path.join(fpath, url[40:])
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
