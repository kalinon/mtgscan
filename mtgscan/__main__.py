import sys
import argparse
from .mtgscan import MtgScan
from .scryfall import ScryFall


def main():
    parser = argparse.ArgumentParser(description='MTG Scan Script')
    parser.add_argument('--update-cache', action='store_true', required=False,
                        help='Will download and cache card images from scryfall.com')
    parser.add_argument('--debug', action='store_true', required=False,
                        help='enable debug')
    parser.add_argument('-s', '--set', type=str, required=False, help='The MTG set to search')
    parser.add_argument('-c', '--camera', default=0, type=int, required=False, help='The Camera to bind to')
    parser.add_argument('-t', '--threshold', default=10, type=int, required=False,
                        help='The threshold to decide a match. Min=1 Max=20')

    args = parser.parse_args()

    if args.update_cache:
        ScryFall.cache_images()
        exit()

    if args.set is None:
        print('Must provide a --set to search!')
        exit(1)

    if args.threshold < 1 or args.threshold > 20:
        print('Must provide a --threshold between 1 and 20!')
        exit(1)

    MtgScan(args.set, args.camera, args.threshold, args.debug).run()
    exit()


if __name__ == '__main__':
    main()
