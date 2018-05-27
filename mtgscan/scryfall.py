import json
import requests
from time import sleep
import urllib.request
import os


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
        response = requests.get(ScryFall.BASE_URI + "/cards/search?order=" + set_code + "&q=e%3Am19&unique=prints")
        return response.json()

    @staticmethod
    def download_image(uri, path):
        sleep(0.07)
        urllib.request.urlretrieve(uri, path)

    @staticmethod
    def cache_images():
        for set_data in ScryFall.get_set_info()['data']:
            print('{} - {}'.format(set_data['code'], set_data['name']))
            set_dir = 'images/' + set_data['code']

            # Make the dir if it does not exist
            try:
                os.stat(set_dir)
            except:
                os.mkdir(set_dir)

            cards_file = set_dir + '/' + set_data['code'] + '.json'

            try:
                os.stat(cards_file)
                card_data = json.load(cards_file)
            except:
                # Now gather all the cards in the set
                card_data = ScryFall.get_set_cards(set_data['code'])

                # Write the response json for caching
                f = open(cards_file, 'w+')
                f.write(json.dumps(card_data))
                f.close()

            if card_data is None:
                print('Unable to get cards for set: {}').format(set_data['name'])
            else:
                if card_data['has_more']:
                    print('Set: {} has more cards!'.format(set_data['name']))
                for card in card_data['data']:
                    image_uri = card['image_uris']['large']
                    image_path = set_dir + '/' + card['id'] + '.jpg'

                    # if the file exits, don't download it again
                    try:
                        os.stat(image_path)
                    except:
                        ScryFall.download_image(image_uri, image_path)
