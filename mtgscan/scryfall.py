import json
import requests
from time import sleep
import urllib.request
import os
import os.path


class ScryFall:
    BASE_URI = "https://api.scryfall.com"

    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def get_set_info():
        sleep(0.07)
        response = requests.get(ScryFall.BASE_URI + "/sets")
        return response.json()

    @staticmethod
    def get_set_cards(set_code):
        sleep(0.07)
        search_url = "{}/cards/search".format(ScryFall.BASE_URI)
        response = requests.get(search_url, params={'order': 'sets', 'q': 's:{}'.format(set_code), 'unique': 'prints'})
        return response.json()

    @staticmethod
    def download_image(uri, path):
        sleep(0.07)
        urllib.request.urlretrieve(uri, path)

    @staticmethod
    def cache_images():
        for set_data in ScryFall.get_set_info()['data']:
            set_code = set_data['code']
            set_name = set_data['name']
            set_dir = 'images/' + set_code
            set_data_file = set_dir + '/' + set_code + '.json'

            print('{} - {}'.format(set_code, set_name))

            # Make the dir if it does not exist
            if not os.path.exists(set_dir):
                os.mkdir(set_dir)

            if os.path.exists(set_data_file):
                f = open(set_data_file, 'r')
                set_card_list = json.load(f)
                f.close()
                ScryFall.cache_set_images(set_code, set_card_list, set_dir)
            else:
                # Now gather all the cards in the set
                set_card_list = ScryFall.get_set_cards(set_code)

                # Write the response json for caching
                f = open(set_data_file, 'w+')
                f.write(json.dumps(set_card_list))
                f.close()
                ScryFall.cache_set_images(set_code, set_card_list, set_dir)

    @staticmethod
    def cache_set_images(set_code, set_card_list, set_dir):
        if set_card_list is None:
            print('Unable to get cards for set: {}').format(set_code)
        else:
            while ScryFall.download_cards(set_card_list, set_dir):
                set_card_list = requests.get(set_card_list['next_page']).json()

    @staticmethod
    def download_cards(set_card_list, set_dir):
        for card_data in set_card_list['data']:
            try:
                image_uri = card_data['image_uris']['large']
                image_path = set_dir + '/' + card_data['id'] + '.jpg'
                # if the file exits, don't download it again
                if not os.path.exists(image_path):
                    ScryFall.download_image(image_uri, image_path)
            except KeyError:
                try:
                    if card_data['card_faces'][0]:
                        image_uri = card_data['card_faces'][0]['image_uris']['large']
                        image_path = set_dir + '/' + card_data['id'] + '.jpg'
                        # if the file exits, don't download it again
                        if not os.path.exists(image_path):
                            ScryFall.download_image(image_uri, image_path)
                except:
                    print("failed to download image for {}".format(card_data))

        return bool(set_card_list['has_more'])
