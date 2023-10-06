import glob
import os
import re
from base64 import urlsafe_b64encode, urlsafe_b64decode

import cv2
import numpy as np

RAW_DIR = "./datasets/stroke-raw"
OUTPUT_DIR = "./datasets/stroke"

# % 123 %
filename_pattern = re.compile(r".*\/tmp1_(\d+)\.jpg")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

for file in os.listdir(RAW_DIR):

    if not os.path.isdir(os.path.join(RAW_DIR, file)):
        print("skip file: ", file)
        continue

    reg_stroke_dir = os.path.join(RAW_DIR, file, "reg_stroke")
    style_stroke_dir = os.path.join(RAW_DIR, file, "style_stroke")
    # make sure it contains reg_stroke and style_stroke
    if not os.path.exists(style_stroke_dir) or \
            not os.path.exists(reg_stroke_dir):
        print("corrupted data: ", file)
        continue


    # read all images from both reg_stroke and style_stroke, crop and save with number-index name
    reg_it = iter(sorted(glob.glob(os.path.join(reg_stroke_dir, "tmp1_*.jpg"))))
    style_it = iter(sorted(glob.glob(os.path.join(style_stroke_dir, "tmp1_*.jpg"))))
    while True:
        try:
            reg_img_file = next(reg_it)
            style_img_file = next(style_it)
        except StopIteration:
            break

        try:
            reg_stroke_idx = int(filename_pattern.match(reg_img_file).group(1))
            style_stroke_idx = int(filename_pattern.match(style_img_file).group(1))
            if reg_stroke_idx != style_stroke_idx:
                raise ValueError("stroke index not match")
        except ValueError:
            print("corrupted data: ", file)
            continue
        except AttributeError:
            print("corrupted data: ", file)
            continue

        img_files = [reg_img_file, style_img_file]
        # mkdir: OUTPUT_DIR/<style_id>/base64_encoded_char/<stroke_idx>.png
        encoded_char_name = urlsafe_b64encode(file.encode("utf-8")).decode("utf-8")
        encoded_char_dir = os.path.join(OUTPUT_DIR, encoded_char_name)
        if not os.path.exists(encoded_char_dir):
            os.makedirs(encoded_char_dir)

        for i, img_file in enumerate(img_files):
            # opencv cannot deal with unicode path, so read it as binary and convert to numpy array
            with open(img_file, "rb") as f:
                img = cv2.imdecode(np.frombuffer(f.read(), np.uint8), cv2.IMREAD_COLOR)

            img_bak = img.copy()
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            th = cv2.threshold(img.copy(), 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            # coords = cv2.findNonZero(th)
            cnts = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            # use the largest contour
            coords = max(cnts[0], key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(coords)

            img = img[y - 5:y + h + 5, x - 5:x + w + 5]
            if img.shape[0] == 0 or img.shape[1] == 0:
                print("corrupted data: ", file)
                continue
            cv2.imwrite(os.path.join(encoded_char_dir, f"s{i}_{reg_stroke_idx}_crop.png"), img)
            cv2.imwrite(os.path.join(encoded_char_dir, f"s{i}_{reg_stroke_idx}_full.png"), img_bak)

