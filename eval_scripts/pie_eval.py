import argparse
import json
from re import U
import numpy as np
import os
from scipy.spatial.distance import cdist
from torch import gt


def parse_args():
    parser = argparse.ArgumentParser(description="Line_Eval")
    parser.add_argument("--preds_bar", dest="preds_bar", help="predictions for bar", default="save/pieout.json", type=str)
    parser.add_argument("--gt_bar", dest="gt_bar", help="groundtruth for bar", default="/home/danny/chartocr_cv/data/piedata(1008)/pie/annotations/instancesPie(1008)_test2019.json", type=str)
    
    args = parser.parse_args()
    return args


def load_preds_gt_json(preds_json_loc, gt_json_loc):
    dp = np.array((18,20))
        
    mm_or_preds = json.load(open(preds_json_loc))
    gt_or_preds = json.load(open(gt_json_loc))
    # Building the table in bottom-up manner

    img_ids = list(mm_or_preds.keys())
    image_ids_in_anno = [{'name':x['file_name'],'id':x['id']} for x in list(gt_or_preds["images"]) if x['file_name'] in img_ids]
    from itertools import groupby
    ids = [x['id'] for x in image_ids_in_anno]
    img_bboxes = [x for x in gt_or_preds["annotations"] if x['image_id'] in ids]
    bbox_list = groupby(img_bboxes, lambda x:x['image_id'])
    f_image_gt = dict()
    for key, group in bbox_list:
        image_name = [x['name'] for x in image_ids_in_anno if x['id'] == key]
        f_image_gt[image_name[0]] = []
        for g in group:
            f_image_gt[image_name[0]].append(g['bbox'])
    

  
    avg_score = 0
    preds,gt = [],[]
    for image_p in f_image_gt: 
        score = 0
        gt_bboxes = f_image_gt[image_p]
        pred_bboxes = mm_or_preds[image_p]
        n = len(gt_bboxes)
        m = len(pred_bboxes)      
        merge_preds = []
       # for pred in pred_bboxes:
        dp =[n][m]      
        for i in range(n+1):
            for j in range(m+1):
                if i==0 or j==0:
                    dp[i][j]=0
                elif preds[i-1]==gt[j-1]:
                    dp[i][j]=1+dp[i-1][j-1]
                else:
                    dp[i][j]=max(
                                dp[i][j-1],
                                dp[i-1][j],
                                (dp[i-1][j-1]) + (1 - abs((preds[i]-gt[j])/gt[j])))
    
    return dp[]    

if __name__ == "__main__":
    args = parse_args()
    #try_metric6a()
    load_preds_gt_json(args.preds_bar,args.gt_bar)