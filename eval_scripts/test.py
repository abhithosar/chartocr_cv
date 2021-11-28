# N = num_of_pred_boxes

# M = num_of_gt_boxes

# K = max(N, M)

# C = pairwise_cost_matrix

# X = assignment_matrix 


## box1, box2, box3, box4, box5, box6 
import torch
num_of_pred_boxes = 6 

pred_boxes = torch.randint(10,20,(6,4)) #6 boxes of random x,y,w,h in range(10,20)
pred_boxes = pred_boxes.repeat_interleave(4, dim=0)
'''

>>> pred_boxes.shape

torch.Size([6, 4])

>>> pred_boxes

tensor([[12, 10, 10, 12],

        [10, 17, 10, 19],

        [18, 17, 15, 10],

        [15, 12, 16, 18],

        [10, 15, 17, 10],

        [19, 10, 14, 18]])

​

>>> pred_boxes = pred_boxes.repeat_interleave(4, dim=0)

>>> pred_boxes.shape

torch.Size([24, 4])

>>> pred_boxes

tensor([[12, 10, 10, 12],

        [12, 10, 10, 12],

        [12, 10, 10, 12],

        [12, 10, 10, 12],

        [10, 17, 10, 19],

        [10, 17, 10, 19],

        [10, 17, 10, 19],

        [10, 17, 10, 19],

        [18, 17, 15, 10],

        [18, 17, 15, 10],

        [18, 17, 15, 10],

        [18, 17, 15, 10],

        [15, 12, 16, 18],

        [15, 12, 16, 18],

        [15, 12, 16, 18],

        [15, 12, 16, 18],

        [10, 15, 17, 10],

        [10, 15, 17, 10],

        [10, 15, 17, 10],

        [10, 15, 17, 10],

        [19, 10, 14, 18],

        [19, 10, 14, 18],

        [19, 10, 14, 18],

        [19, 10, 14, 18]])

'''

## boxA, boxB, boxC, boxD

num_of_gt_boxes = 4

gt_boxes = torch.randint(10,20,(4,4)) # 4 boxes of random x,y,w,h in range(10,20)
gt_boxes = gt_boxes.repeat(6, 1) 
'''

>>> gt_boxes.shape

torch.Size([4, 4])

>>> gt_boxes 

tensor([[13, 10, 15, 14],

        [15, 16, 12, 16],

        [18, 12, 12, 16],

        [18, 14, 17, 18]])

​

>>> gt_boxes = gt_boxes.repeat(6, 1) 

>>> gt_boxes.shape

torch.Size([24, 4])

>>> gt_boxes.repeat(6, 1) 

tensor([[13, 10, 15, 14],

        [15, 16, 12, 16],

        [18, 12, 12, 16],

        [18, 14, 17, 18],

        [13, 10, 15, 14],

        [15, 16, 12, 16],

        [18, 12, 12, 16],

        [18, 14, 17, 18],

        [13, 10, 15, 14],

        [15, 16, 12, 16],

        [18, 12, 12, 16],

        [18, 14, 17, 18],

        [13, 10, 15, 14],

        [15, 16, 12, 16],

        [18, 12, 12, 16],

        [18, 14, 17, 18],

        [13, 10, 15, 14],

        [15, 16, 12, 16],

        [18, 12, 12, 16],

        [18, 14, 17, 18],

        [13, 10, 15, 14],

        [15, 16, 12, 16],

        [18, 12, 12, 16],

        [18, 14, 17, 18]])

'''

cos = torch.nn.CosineSimilarity(dim=1, eps=1e-6) # cost function replace this with equation 9

pairwise_cost_matrix = cos(pred_boxes.float(), gt_boxes.float())

pairwise_cost_matrix = pairwise_cost_matrix.reshape(4, -1)


## matching : say box1 match boxA, box2 match nothing,  box3 match boxB, box4 match nothig, box5 match boxC, box6 match boxD, 

# one hot encode from gt by neearest coordinate / iou (try both?) (For each pred which is best gt box)

assignment_matrix = [1, 0, 0, 0] + [0, 0, 0, 0]  + [0, 1, 0, 0] + [0, 0, 0, 0] + [0, 0, 1, 0] + [0, 0, 0, 1]

X = torch.tensor(assignment_matrix)

X = X.reshape(4, -1)

assigned_cost = pairwise_cost_matrix * X


max_scores, idx = torch.max((1-pairwise_cost_matrix)/6, dim=1)

total_score = max_scores.sum()


'''

>>> pairwise_cost_matrix = cos(pred_boxes.float(), gt_boxes.float())

>>> pairwise_cost_matrix

tensor([0.9892, 0.9944, 0.9956, 0.9979, 0.9349, 0.9776, 0.9407, 0.9477, 0.9559,

        0.9702, 0.9620, 0.9671, 0.9973, 0.9810, 0.9850, 0.9972, 0.9617, 0.9507,

        0.9197, 0.9551, 0.9833, 0.9692, 0.9948, 0.9903])

>>> pairwise_cost_matrix.shape

torch.Size([24])

​

>>> pairwise_cost_matrix = pairwise_cost_matrix.reshape(4, -1)

>>> pairwise_cost_matrix.shape

torch.Size([4, 6])

>>> pairwise_cost_matrix

tensor([[0.9892, 0.9944, 0.9956, 0.9979, 0.9349, 0.9776],

        [0.9407, 0.9477, 0.9559, 0.9702, 0.9620, 0.9671],

        [0.9973, 0.9810, 0.9850, 0.9972, 0.9617, 0.9507],

        [0.9197, 0.9551, 0.9833, 0.9692, 0.9948, 0.9903]])

​

​

>>> assignment_matrix = [1, 0, 0, 0] + [0, 0, 0, 0]  + [0, 1, 0, 0] + [0, 0, 0, 0] + [0, 0, 1, 0] + [0, 0, 0, 1]

>>> X = torch.tensor(assignment_matrix)

>>> X.shape

torch.Size([24])

>>> pairwise_cost_matrix

tensor([[0.9892, 0.9944, 0.9956, 0.9979, 0.9349, 0.9776],

        [0.9407, 0.9477, 0.9559, 0.9702, 0.9620, 0.9671],

        [0.9973, 0.9810, 0.9850, 0.9972, 0.9617, 0.9507],

        [0.9197, 0.9551, 0.9833, 0.9692, 0.9948, 0.9903]])

>>> X = X.reshape(4, -1)

>>> X.shape

torch.Size([4, 6])

​

>>> assigned_cost = pairwise_cost_matrix * X

>>> assigned_cost

tensor([[0.9892, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],

        [0.0000, 0.0000, 0.0000, 0.9702, 0.0000, 0.0000],

        [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],

        [0.9197, 0.0000, 0.0000, 0.0000, 0.0000, 0.9903]])

​

​

>>> K

6

## Avg Score per box

>>> (1-assigned_cost)/6

tensor([[0.0018, 0.1667, 0.1667, 0.1667, 0.1667, 0.1667],

        [0.1667, 0.1667, 0.1667, 0.0050, 0.1667, 0.1667],

        [0.1667, 0.1667, 0.1667, 0.1667, 0.1667, 0.1667],

        [0.0134, 0.1667, 0.1667, 0.1667, 0.1667, 0.0016]])

​

## Maximise score is same as minimise cost 

>>> max_scores, idx = torch.max((1-pairwise_cost_matrix)/6, dim=1)

>>> max_scores

tensor([0.0108, 0.0099, 0.0082, 0.0134])

>>> total_score = max_scores.sum()

>>> total_score

tensor(0.0423)

​

>>> max_scores, idx = torch.max((1-assigned_cost)/6, dim=1)

>>> max_scores

tensor([0.1667, 0.1667, 0.1667, 0.1667])

>>> max_scores.sum()

tensor(0.6667)

​

'''