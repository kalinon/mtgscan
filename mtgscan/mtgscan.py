import cv2
import numpy as np
import json
from PIL import Image, ImageFilter
from glob import glob
import imagehash


class MtgScan:

    def __init__(self, set_code, cam_num=0, threshold=10, debug=False) -> None:
        self.cap = cv2.VideoCapture(cam_num)
        self.sorted_contours = []
        self.frame = None
        self.threshold = threshold
        self.set_code = set_code
        self.debug = debug

    def run(self):
        while True:
            _, self.frame = self.cap.read()

            # Convert to grey scale
            gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

            # Create Threshold
            _, thresh = cv2.threshold(gray, 130, 255, cv2.THRESH_BINARY)

            # Find Contours
            self.sorted_contours = self.find_contours(thresh)

            # Identify a contour that is a card (or most likely)
            card_contour, card_image, maxWidth, maxHeight = self.find_card_contour()

            if card_contour is not None:
                cv2.drawContours(self.frame, [card_contour], -1, (0, 255, 0), 2)
                cv2.imshow("card?", card_image)

            # Render Frame
            self.render()

            if cv2.waitKey(1) == ord('c') and card_image is not None:
                self.identify_card(self.set_code, card_image, maxWidth, maxHeight, self.threshold)

            if cv2.waitKey(1) == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

    def render(self):
        cv2.imshow("frame", self.frame)

    def draw_contours(self, contours):
        for _, contour in contours:
            cv2.drawContours(self.frame, [contour], -1, (0, 255, 0), 2)

    def find_card_contour(self):
        if self.sorted_contours is None:
            return
        for _, contour in self.sorted_contours:
            dst, max_height, max_width, rect = self.warp_contour(contour)

            if max_width == 0 or max_height == 0:
                continue

            ratio = max_height / max_width
            if (ratio >= 0.730 or ratio <= 0.739) and dst[2][0] < 1200 and dst[2][1] < 1200:
                if self.debug:
                    print(ratio)
                M = cv2.getPerspectiveTransform(rect, dst)
                return contour, cv2.warpPerspective(self.frame, M, (max_width, max_height)), max_width, max_height

    def warp_contour(self, card_contour):
        # create a min area rectangle from our contour
        _rect = cv2.minAreaRect(card_contour)
        box = cv2.boxPoints(_rect)
        box = np.int0(box)

        # create empty initialized rectangle
        rect = np.zeros((4, 2), dtype="float32")

        # get top left and bottom right points
        s = box.sum(axis=1)
        rect[0] = box[np.argmin(s)]
        rect[2] = box[np.argmax(s)]

        # get top right and bottom left points
        diff = np.diff(box, axis=1)
        rect[1] = box[np.argmin(diff)]
        rect[3] = box[np.argmax(diff)]

        (tl, tr, br, bl) = rect

        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))

        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]], dtype="float32")
        return dst, maxHeight, maxWidth, rect

    @staticmethod
    def get_contour_points(contour):
        rect = cv2.minAreaRect(contour)
        points = cv2.boxPoints(rect)
        points = np.int0(points)
        return points

        # for point in points:
        #     cv2.circle(self.frame, tuple(point), 10, (0, 255, 0), -1)

    @staticmethod
    def find_contours(thresh):
        _, contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return sorted([(cv2.contourArea(i), i) for i in contours], key=lambda a: a[0], reverse=True)

    @staticmethod
    def identify_card(set_code, card, max_width, max_height, threshold=10):
        # hash our warped image
        hash = imagehash.average_hash(Image.fromarray(card))

        images = []
        # loop over all official images
        for orig in glob('images/{}/*.jpg'.format(set_code)):
            # grayscale, resize, and blur original image
            orig_image = Image.open(orig).convert('LA')
            orig_image.resize((max_width, max_height))
            orig_image.filter(ImageFilter.BLUR)

            # hash original and get hash
            orig_hash = imagehash.average_hash(orig_image)
            score = hash - orig_hash
            if score <= threshold:
                images.append({'file': orig, 'score': score})
                print('Comparing image to {}, score {}'.format(
                    orig, score
                ))
        print('-' * 50)
        if len(images) > 0:
            best_match = sorted(images, key=lambda k: k['score'])[0]
            print('Best match is file: {} with score of: {}'.format(best_match['file'], best_match['score']))
            print('-' * 50)
