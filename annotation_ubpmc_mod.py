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
parser.add_argument("--path", help="Path to clean empty JSON", default="save/horizontal_bar_ubpmc.json")
parser.add_argument("--type", help="Chart Type", default="horizontal bar")

args = parser.parse_args()
print(args.path)
#full_path = os.path.join(args.path, "annotations_JSON", "*", "*.json")
#print(full_path)
file = args.path
f = open(file)
data = json.load(f)

for key in data.keys():
    new_dict = {}
    new_dict["task1"] = {}
    new_dict["task6"] = {}
    file_name = key
    file_name = os.path.splitext(os.path.basename(file_name))[0] + ".json"
    vals = data[key]
    if args.type == "line":
        new_dict["task1"] = {"output": {"chart_type" : "line"}}
        list_vals = []
        main_list = []
        for val in vals:
            for inner_val in val:
                list_vals.append({"x": inner_val[0], "y":inner_val[1]})
            main_list.append(list_vals)
        new_dict["task6"] = {"output": {"visual elements": {"lines": main_list}}}
    target_path = os.path.join("annotation_convert", args.type)
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    target_path = os.path.join(target_path,file_name)
    with open(target_path, 'w') as fp:
        json.dump(new_dict, fp)
    if args.type == "scatter":
        new_dict["task1"] = {"output": {"chart_type" : "scatter"}}
        list_vals = []
        main_list = []
        for val in vals:
            for inner_val in val:
                list_vals.append({"x": inner_val[0], "y":inner_val[1]})
            main_list.append(list_vals)
        new_dict["task6"] = {"output": {"visual elements": {"scatter points": main_list}}}
    target_path = os.path.join("annotation_convert", args.type)
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    target_path = os.path.join(target_path,file_name)
    with open(target_path, 'w') as fp:
        json.dump(new_dict, fp)


    if args.type == "vertical bar":
        new_dict["task1"] = {"output": {"chart_type" : "vertical bar"}}
        list_vals = []
        main_list = []
        for val in vals:
            list_vals.append({"height": val[3]-val[1], "width": val[2]-val[0],"x0": val[0], "y0":val[1]})
            #main_list.append(list_vals)
        new_dict["task6"] = {"output": {"visual elements": {"bars": list_vals}}}
    target_path = os.path.join("annotation_convert", args.type)
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    target_path = os.path.join(target_path,file_name)
    with open(target_path, 'w') as fp:
        json.dump(new_dict, fp)


    if args.type == "horizontal bar":
        new_dict["task1"] = {"output": {"chart_type" : "horizontal bar"}}
        list_vals = []
        main_list = []
        for val in vals:
            list_vals.append({"height": val[3]-val[1], "width": val[2]-val[0],"x0": val[0], "y0":val[1]})
            #main_list.append(list_vals)
        new_dict["task6"] = {"output": {"visual elements": {"bars": list_vals}}}
    target_path = os.path.join("annotation_convert", args.type)
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    target_path = os.path.join(target_path,file_name)
    with open(target_path, 'w') as fp:
        json.dump(new_dict, fp)
