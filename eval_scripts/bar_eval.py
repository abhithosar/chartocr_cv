import argparse
import json
import numpy as np
import os

from torch import gt

def parse_args():
    parser = argparse.ArgumentParser(description="Bar_Eval")
    parser.add_argument("--preds_bar", dest="preds_bar", help="predictions for bar", default="save/barout_exp.json", type=str)
    parser.add_argument("--gt_bar", dest="gt_bar", help="groundtruth for bar", default="data/bardata(1031)/bar/annotations/instancesBar(1031)_test2019.json", type=str)
    args = parser.parse_args()
    return args


def load_preds_gt_json(preds_json_loc, gt_json_loc):
    preds_json = json.load(open(preds_json_loc))
    preds_json_mod = dict()
    for i in preds_json:
        preds_json_mod[i] = []
        for bbx in preds_json[i]:
            newbbox = [bbx[0],bbx[1],bbx[2]-bbx[0],bbx[3]-bbx[1]]
            preds_json_mod[i].append(newbbox)    
    preds_json = preds_json_mod
    preds_json_mod =None
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
        f_image_gt[image_name[0]] = []
        for g in group:
            f_image_gt[image_name[0]].append(g['bbox'])
            print(g)
            #= [g['bbox'] for g in group]
        #[f_image_gt[image_name].append(item) for item in group]#group

    image_pred_gt_map = dict()
    for image in f_image_gt:
        image_pred_gt_map[image] = []
        for bbox in f_image_gt[image]:
            max_area = -1
            max_index = 0 
            index = 0
            for p_bbox in preds_json[image]:
                xa = max(bbox[0],p_bbox[0])
                ya = max(bbox[1],p_bbox[1])

                xb = max(bbox[0]+bbox[2],p_bbox[0],p_bbox[2])
                yb = max(bbox[1]+bbox[3],p_bbox[1],p_bbox[3])
                area = max((xb - xa + 1), 0) * max((yb - ya + 1), 0)
                # x_dist = min(bbox[0]+bbox[2],p_bbox[0]+p_bbox[2]) - max(bbox[0],p_bbox[0])
                # y_dist = min(bbox[1],p_bbox[1]) - max(bbox[1]+bbox[3],p_bbox[1]+p_bbox[3]) 
                if(max_area < (area)):
                    max_area = area
                    max_index = index
                index += 1
            if max_index > -1 and max_area > -1:
                match_tuple = (bbox,preds_json[image][max_index])
            else:
                match_tuple = (0,0,0,0)    
            image_pred_gt_map[image].append(match_tuple)


    #Make pairs of maximum overlapping rectangles
    #Calculate according to formula
    i = 9
    #bboxes_annons = [x for x in preds_json["annotations"] if x.] 



if __name__ == "__main__":
    args = parse_args()
    load_preds_gt_json(args.preds_bar,args.gt_bar)


    