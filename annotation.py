# -*- coding: utf-8 -*-
"""
Created on Fri Nov 26 19:11:44 2021

@author: Vaibhav Rao
"""

import json
import glob
import os
import argparse

parser = argparse.ArgumentParser(description="Clean UBPMC")
parser.add_argument("--path", help="Path to clean empty JSON", default="data/ICPR2020_CHARTINFO_UB_PMC_TRAIN_v1.21/annotations_JSON")

args = parser.parse_args()
print(args.path)
full_path = os.path.join(args.path, "*", "*.json")
print(full_path)

all_files = glob.glob(full_path)
for file in all_files:
    #if file == all_files[528]:
    with open(file) as f:
        data = json.load(f)
        f.close()
        if (not "task6" in data) or (data["task6"]==None):
            #print("None for File:", file)
            os.remove(file)