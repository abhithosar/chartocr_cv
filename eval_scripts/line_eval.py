import argparse
import json
from re import U
import numpy as np
import os
from scipy.spatial.distance import cdist
from torch import gt


def parse_args():
    parser = argparse.ArgumentParser(description="Line_Eval")
    parser.add_argument("--preds_bar", dest="preds_bar", help="predictions for bar", default="save/lineout_full.json", type=str)
    parser.add_argument("--gt_bar", dest="gt_bar", help="groundtruth for bar", default="data/linedata(1028)/line/annotations/instancesLine(1023)_test2019.json", type=str)
    
    args = parser.parse_args()
    return args

def check_groups(ds):
    try:
        _i = ds[0][0]
        return 1
    except Exception:
        return 0

def compare_line(pred_ds, gt_ds):
    is_grouped = check_groups(gt_ds)
    if is_grouped:
        score = np.zeros((len(gt_ds), len(pred_ds)))
        for iter_seq1 in range(len(gt_ds)):
            for iter_seq2 in range(len(pred_ds)):
                score[iter_seq1, iter_seq2] = compare_continuous(gt_ds[iter_seq1], pred_ds[iter_seq2])
        from scipy.optimize import  linear_sum_assignment
        row_ind, col_ind = linear_sum_assignment(-score)
        score = score[row_ind, col_ind].sum()/len(gt_ds)
    else:
        print(gt_ds)
        score = compare_continuous(pred_ds, gt_ds)

    return score

def get_cont_recall(p_xs, p_ys, g_xs, g_ys, epsilon):
    total_score = 0
    total_interval = 0

    for i in range(g_xs.shape[0]):
        x = g_xs[i]
        
        if g_xs.shape[0] == 1:
            interval = 1
        elif i == 0:
            interval = (g_xs[i+1] - x) / 2
        elif i == (g_xs.shape[0] - 1):
            interval = (x - g_xs[i-1]) / 2
        else:
            interval = (g_xs[i+1] - g_xs[i-1]) / 2

        y = g_ys[i]
        y_interp = np.interp(x, p_xs, p_ys)
        error = min(1, abs( (y - y_interp) / (abs(y) + epsilon)))
        total_score += (1 - error) * interval
        total_interval += interval

    if g_xs.shape[0] != 1:
        assert np.isclose(total_interval, g_xs[-1] - g_xs[0])
    return total_score / total_interval

def compare_continuous(pred_ds, gt_ds):
    pred_ds = sorted(pred_ds, key=lambda p: float(p['x']))
    gt_ds = sorted(gt_ds, key=lambda p: float(p['x']))

    if not pred_ds and not gt_ds:
        # empty matches empty
        return 1.0
    elif not pred_ds and gt_ds:
        # empty does not match non-empty
        return 0.0
    elif pred_ds and not gt_ds:
        # empty does not match non-empty
        return 0.0

    p_xs = np.array([float(ds['x']) for ds in pred_ds])
    p_ys = np.array([float(ds['y']) for ds in pred_ds])
    g_xs = np.array([float(ds['x']) for ds in gt_ds])
    g_ys = np.array([float(ds['y']) for ds in gt_ds])

    epsilon = (g_ys.max() - g_ys.min()) / 100.
    recall = get_cont_recall(p_xs, p_ys, g_xs, g_ys, epsilon)
    precision = get_cont_recall(g_xs, g_ys, p_xs, p_ys, epsilon)

    return (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.



def get_dataseries(json_obj):
    if 'task6_output' in json_obj:
        return json_obj['task6_output']['visual elements']
    elif 'task6' in json_obj:
        return json_obj['task6']['output']['visual elements']
    return None


def load_preds_gt_json(preds_json_loc, gt_json_loc):
    #preds_json = json.load(open("/home/danny/Downloads/release_ICPR2020_CHARTINFO_UB_PMC_TRAIN_v1.21/ICPR2020_CHARTINFO_UB_PMC_TRAIN_v1.21/annotations_JSON/line/PMC5554038___materials-10-00657-g005.json"))#preds_json_loc))
    #gt_json = json.load(open("/home/danny/Downloads/release_ICPR2020_CHARTINFO_UB_PMC_TRAIN_v1.21/ICPR2020_CHARTINFO_UB_PMC_TRAIN_v1.21/annotations_JSON/line/PMC5554038___materials-10-00657-g005.json"))#gt_json_loc))
    
    mm_or_preds = json.load(open(preds_json_loc))
    gt_or_preds = json.load(open(gt_json_loc))



    #pred_no_names = get_dataseries(preds_json)['lines']
    #gt_no_names = get_dataseries(gt_json)['lines']
    
    
   #gt_json = json.load(open(gt_json_loc))
    i = 0
    preds_transform = dict()
    for key in mm_or_preds:
        preds_transform[key] = []
        for line in mm_or_preds[key]:
            pts = []
            for pt in line:
                pts.append({'x':pt[0],'y':pt[1]})
            preds_transform[key].append(pts)
            i = 0
    img_ids = list(mm_or_preds.keys())
    print(img_ids)
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
            line_pts = g['bbox']
            x_vals = line_pts[::2]
            y_vals = line_pts[1::2]
            line_cords = []
            for x,y in zip(x_vals,y_vals):
                if x != 0 and y != 0:
                    line_cords.append({'x':x,'y':y})
            if len(line_cords) > 0:
                f_image_gt[image_name[0]].append(line_cords)
    
    scores = list()
    for image_p in f_image_gt:
        gt_bboxes = f_image_gt[image_p]
        pred_bboxes = preds_transform[image_p]
        
        ds_match_score = compare_line(pred_bboxes, gt_bboxes)
        print(ds_match_score)
        scores.append(ds_match_score)
    
    avg_score = sum(scores) / len(scores)
    print("Avg Score: ",avg_score)
    
    df = 0
if __name__ == "__main__":
    args = parse_args()
    #try_metric6a()
    load_preds_gt_json(args.preds_bar,args.gt_bar)