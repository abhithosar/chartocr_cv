import os
import cv2
import json
import numpy as np
import torch
import matplotlib.pyplot as plt
from tqdm import tqdm
from config import system_configs
from utils import crop_image, normalize_
import external.nms as nms
def _rescale_dets(detections, ratios, borders, sizes):
    xs, ys = detections[..., 0:4:2], detections[..., 1:4:2]
    xs    /= ratios[:, 1][:, None, None]
    ys    /= ratios[:, 0][:, None, None]
    xs    -= borders[:, 2][:, None, None]
    ys    -= borders[:, 0][:, None, None]
    np.clip(xs, 0, sizes[:, 1][:, None, None], out=xs)
    np.clip(ys, 0, sizes[:, 0][:, None, None], out=ys)

def _rescale_points(dets, ratios, borders, sizes):
    xs, ys = dets[:, :, 3], dets[:, :, 4]
    xs    /= ratios[0, 1]
    ys    /= ratios[0, 0]
    xs    -= borders[0, 2]
    ys    -= borders[0, 0]
    np.clip(xs, 0, sizes[0, 1], out=xs)
    np.clip(ys, 0, sizes[0, 0], out=ys)

def save_image(data, fn):
    sizes = np.shape(data)
    height = float(sizes[0])
    width = float(sizes[1])

    fig = plt.figure()
    fig.set_size_inches(width/height, 1, forward=False)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)

    ax.imshow(data)
    plt.savefig(fn, dpi = height)
    plt.close()

def kp_decode(nnet, images, K, tl_gt, br_gt, ae_threshold=0.5, kernel=3):
    with torch.no_grad():
        try:
            detections, detections_tl, detections_br = nnet.test([images], tl_gt=tl_gt, br_gt=br_gt, ae_threshold=ae_threshold, K=K, kernel=kernel)
            detections_num = detections.data.cpu().numpy()
            detections_tl = detections_tl.data.cpu().numpy().transpose((2, 1, 0))
            detections_br = detections_br.data.cpu().numpy().transpose((2, 1, 0))
            del detections
            return detections_num, detections_tl, detections_br, True
        except Exception as e:
            print(e)
            torch.cuda.empty_cache()
            return None, None, None, False


def kp_detection(db, nnet, result_dir, debug=False, decode_func=kp_decode):
    result_json = os.path.join(result_dir, "results.json")
    point_json_tl = os.path.join(result_dir, "points_tl.json")
    point_json_br = os.path.join(result_dir, "points_br.json")
    debug_dir = os.path.join(result_dir, "debug")
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)
    db_inds = db.db_inds
    num_images = db_inds.size

    K = db.configs["top_k"]
    ae_threshold = db.configs["ae_threshold"]
    nms_kernel = db.configs["nms_kernel"]

    scales = db.configs["test_scales"]
    weight_exp = db.configs["weight_exp"]
    merge_bbox = db.configs["merge_bbox"]
    categories = db.configs["categories"]
    nms_threshold = db.configs["nms_threshold"]
    max_per_image = db.configs["max_per_image"]
    nms_algorithm = {
        "nms": 0,
        "linear_soft_nms": 1,
        "exp_soft_nms": 2
    }[db.configs["nms_algorithm"]]
    if True:

        top_bboxes = {}
        top_points_tl = {}
        top_points_br = {}
        for ind in tqdm(range(0, num_images), ncols=80, desc="locating kps"):
            db_ind = db_inds[ind]
            image_id   = db.image_ids(db_ind)
            image_file = db.image_file(db_ind)
            image      = cv2.imread(image_file)
            print(image_file)
            detections_gt = db.detections(db_ind)
            height, width = image.shape[0:2]

            detections = []
            detections_point_tl = []
            detections_point_br = []
            for scale in scales:
                new_height = int(height * scale)
                new_width  = int(width * scale)
                new_center = np.array([new_height // 2, new_width // 2])

                inp_height = new_height | 127
                inp_width  = new_width  | 127
                images  = np.zeros((1, 3, inp_height, inp_width), dtype=np.float32)
                ratios  = np.zeros((1, 2), dtype=np.float32)
                borders = np.zeros((1, 4), dtype=np.float32)
                sizes   = np.zeros((1, 2), dtype=np.float32)

                out_height, out_width = (inp_height + 1) // 4, (inp_width + 1) // 4
                height_ratio = out_height / inp_height
                width_ratio  = out_width  / inp_width

                resized_image = cv2.resize(image, (new_width, new_height))
                resized_image, border, offset = crop_image(resized_image, new_center, [inp_height, inp_width])

                resized_image = resized_image / 255.
                normalize_(resized_image, db.mean, db.std)

                images[0]  = resized_image.transpose((2, 0, 1))
                borders[0] = border
                sizes[0]   = [int(height * scale), int(width * scale)]
                ratios[0]  = [height_ratio, width_ratio]

                tl_gt = []
                br_gt = []
                for det in detections_gt:
                    #print(det)
                    tl_gt.append([int((det[0]+borders[0, 2])*ratios[0, 1]), int((det[1]+borders[0, 0])*ratios[0, 0]), det[4]-1])
                    br_gt.append([int((det[2]+borders[0, 2])*ratios[0, 1]), int((det[3]+borders[0, 0])*ratios[0, 0]), det[4]-1])
                tl_gt = torch.from_numpy(np.expand_dims(np.array(tl_gt), 0))
                br_gt = torch.from_numpy(np.expand_dims(np.array(br_gt), 0))
                images = torch.from_numpy(images)
                dets, dets_tl, dets_br, flag = decode_func(nnet, images, K, tl_gt=tl_gt, br_gt=br_gt, ae_threshold=ae_threshold, kernel=nms_kernel)
                #print(0)
                #print(dets_tl.shape)
                if not flag:
                    print("error when try to test %s" %image_file)
                    continue
                ratio_height = inp_height / out_height * height / new_height
                ratio_width = inp_width / out_width * width / new_width
                dets   = dets.reshape(1, -1, 8)

                _rescale_dets(dets, ratios, borders, sizes)
                _rescale_points(dets_tl, ratios, borders, sizes)
                _rescale_points(dets_br, ratios, borders, sizes)
                dets[:, :, 0:4] /= scale
                detections.append(dets)
                detections_point_tl.append(dets_tl)
                detections_point_br.append(dets_br)
            if len(detections)==0:
                continue
            detections = np.concatenate(detections, axis=1)
            detections_point_tl = np.concatenate(detections_point_tl, axis=1)
            detections_point_br = np.concatenate(detections_point_br, axis=1)
            #print('1')
            #print(detections_point.shape)
            classes    = detections[..., -1]
            classes    = classes[0]
            detections = detections[0]

            classes_p_tl = detections_point_tl[:, 0, 2]
            classes_p_br = detections_point_br[:, 0, 2]
            #print('2')
            #print(classes_p.shape)

            # reject detections with negative scores
            keep_inds  = (detections[:, 4] > -1)
            detections = detections[keep_inds]
            classes    = classes[keep_inds]

            keep_inds_p = (detections_point_tl[:, 0, 0] > 0)
            detections_point_tl = detections_point_tl[keep_inds_p, 0]
            classes_p_tl = classes_p_tl[keep_inds_p]

            keep_inds_p = (detections_point_br[:, 0, 0] > 0)
            detections_point_br = detections_point_br[keep_inds_p, 0]
            classes_p_br = classes_p_br[keep_inds_p]

            #print('3')
            #print(detections_point.shape)

            top_bboxes[image_id] = {}
            top_points_tl[image_id] = {}
            top_points_br[image_id] = {}
            for j in range(categories):
                keep_inds = (classes == j)
                top_bboxes[image_id][j + 1] = detections[keep_inds][:, 0:7].astype(np.float32)
                if merge_bbox:
                    nms.soft_nms_merge(top_bboxes[image_id][j + 1], Nt=nms_threshold, method=nms_algorithm, weight_exp=weight_exp)
                else:
                    nms.soft_nms(top_bboxes[image_id][j + 1], Nt=nms_threshold, method=nms_algorithm)
                top_bboxes[image_id][j + 1] = top_bboxes[image_id][j + 1][:, 0:5]

                keep_inds_p = (classes_p_tl == j)
                top_points_tl[image_id][j + 1] = detections_point_tl[keep_inds_p].astype(np.float32)
                keep_inds_p = (classes_p_br == j)
                top_points_br[image_id][j + 1] = detections_point_br[keep_inds_p].astype(np.float32)
                #print(top_points[image_id][j + 1][0])

            scores = np.hstack([
                top_bboxes[image_id][j][:, -1]
                for j in range(1, categories + 1)
            ])
            if len(scores) > max_per_image:
                kth    = len(scores) - max_per_image
                thresh = np.partition(scores, kth)[kth]
                for j in range(1, categories + 1):
                    keep_inds = (top_bboxes[image_id][j][:, -1] >= thresh)
                    top_bboxes[image_id][j] = top_bboxes[image_id][j][keep_inds]

            scores = np.hstack([
                top_points_tl[image_id][j][:, 0]
                for j in range(1, categories + 1)
            ])
            if len(scores) > max_per_image:
                kth = len(scores) - max_per_image
                thresh = np.partition(scores, kth)[kth]
                for j in range(1, categories + 1):
                    keep_inds = (top_points_tl[image_id][j][:, 0] >= thresh)
                    top_points_tl[image_id][j] = top_points_tl[image_id][j][keep_inds]

            scores = np.hstack([
                top_points_br[image_id][j][:, 0]
                for j in range(1, categories + 1)
            ])
            if len(scores) > max_per_image:
                kth = len(scores) - max_per_image
                thresh = np.partition(scores, kth)[kth]
                for j in range(1, categories + 1):
                    keep_inds = (top_points_br[image_id][j][:, 0] >= thresh)
                    top_points_br[image_id][j] = top_points_br[image_id][j][keep_inds]

            if debug:
                image_file = db.image_file(db_ind)
                image      = cv2.imread(image_file)

                bboxes = {}
                for j in range(1, categories + 1):
                    keep_inds = (top_bboxes[image_id][j][:, -1] > 0.5)
                    cat_name  = db.class_name(j)
                    cat_size  = cv2.getTextSize(cat_name, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                    color     = np.random.random((3, )) * 0.6 + 0.4
                    color     = color * 255
                    color     = color.astype(np.int32).tolist()
                    for bbox in top_bboxes[image_id][j][keep_inds]:
                        bbox  = bbox[0:4].astype(np.int32)
                        if bbox[1] - cat_size[1] - 2 < 0:
                            cv2.rectangle(image,
                                (bbox[0], bbox[1] + 2),
                                (bbox[0] + cat_size[0], bbox[1] + cat_size[1] + 2),
                                color, -1
                            )
                            cv2.putText(image, cat_name,
                                (bbox[0], bbox[1] + cat_size[1] + 2),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), thickness=1
                            )
                        else:
                            cv2.rectangle(image,
                                (bbox[0], bbox[1] - cat_size[1] - 2),
                                (bbox[0] + cat_size[0], bbox[1] - 2),
                                color, -1
                            )
                            cv2.putText(image, cat_name,
                                (bbox[0], bbox[1] - 2),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), thickness=1
                            )
                        cv2.rectangle(image,
                            (bbox[0], bbox[1]),
                            (bbox[2], bbox[3]),
                            color, 2
                        )
                debug_file = os.path.join(debug_dir, "{}.jpg".format(db_ind))

        detections  = db.convert_to_coco(top_bboxes)
        detections_point_tl = db.convert_to_coco_points(top_points_tl)
        detections_point_br = db.convert_to_coco_points(top_points_br)
        with open(result_json, "w") as f:
            json.dump(detections, f)
        with open(point_json_tl, "w") as f:
            json.dump(detections_point_tl, f)
        with open(point_json_br, "w") as f:
            json.dump(detections_point_br, f)

    #image_ids = [db.image_ids(ind) for ind in db_inds]
    #with open(result_json, "r") as f:
        #result_json = json.load(f)
    #for cls_type in range(1, categories+1):
        #db.evaluate(result_json, [cls_type], image_ids)
    return 0

def testing(db, nnet, result_dir, debug=False):
    return globals()[system_configs.sampling_function](db, nnet, result_dir, debug=debug)
