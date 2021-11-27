import argparse
import json
import numpy as np
import os

from torch import gt

def parse_args():
    parser = argparse.ArgumentParser(description="Bar_Eval")
    parser.add_argument("--preds_bar", dest="preds_bar", help="predictions for bar", default="save/barout_o.json", type=str)
    parser.add_argument("--gt_bar", dest="gt_bar", help="groundtruth for bar", default="data/bardata(1031)/bar/annotations/instancesBar(1031)_test2019.json", type=str)
    args = parser.parse_args()
    return args


def load_preds_gt_json(preds_json_loc, gt_json_loc):
    preds_json = json.load(open(preds_json_loc))
    gt_json = json.load(open(gt_json_loc))
    i = 0
    img_ids = list(preds_json.keys())
    print(img_ids)
    image_ids_in_anno = [{'name':x['file_name'],'id':x['id']} for x in list(gt_json["images"]) if x['file_name'] in img_ids]
    from itertools import groupby
    ids = [x['id'] for x in image_ids_in_anno]
    img_bboxes = [x for x in gt_json["annotations"] if x['image_id'] in ids]
    bbox_list = groupby(img_bboxes, lambda x:x['image_id'])
    f_image_gt = dict()
    for key, group in bbox_list:
        image_name = [x['name'] for x in image_ids_in_anno if x['id'] == key]
        for g in group:
            print(g)
        f_image_gt[image_name] = [x['bbox'] for x in group]
        #[f_image_gt[image_name].append(item) for item in group]#group
    i = 9
    #bboxes_annons = [x for x in preds_json["annotations"] if x.] 



if __name__ == "__main__":
    args = parse_args()
    load_preds_gt_json(args.preds_bar,args.gt_bar)


    