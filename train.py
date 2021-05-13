import torch 
import torchvision.transforms as transforms
import torch.optim as optim
import torchvision.transforms.functional as FT 
from tqdm import tqdm
from torch.utils.data import DataLoader
from model import Yolov1
from dataset import VOCDataset
from utils import (
    intersection_over_union,
    non_max_suppression,
    mean_average_precision,
    cellboxes_to_boxes,
    get_bboxes,
    plot_image,
    save_checkpoint,
    load_checkpoint)
import numpy as np
from loss import YoloLoss
from loss2 import YoloLoss2

seed = 1
torch.manual_seed(seed)

LEARNING_RATE = 2e-5
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 8
WEIGHT_DECAY = 0
EPOCHS = 1
NUM_WORKERS = 2
PIN_MEMORY = True
LOAD_MODEL = False
LOAD_MODEL_FILE = "None"
IMG_DIR = "data/images"
LABEL_DIR = "data/labels"

class Compose(object):
    def __init__(self, transforms):
        self.transforms = transforms

    def __call__(self, img, bboxes):
        for t in self.transforms:
            img, bboxes = t(img), bboxes
        
        return img, bboxes
transform = Compose([transforms.Resize((448,448)), transforms.ToTensor()])
def train_fn(train_loader, model, optimizer, loss_fn):
    loop = tqdm(train_loader, leave=True)
    mean_loss = []

    for batch_idx, (x,y) in enumerate(loop):
        x, y = x, y
        out = model(x)
        loss = loss_fn(out,y)
        mean_loss.append(loss.item())
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        loop.set_postfix(loss = loss.item())
    print(f"Mean loss: {sum(mean_loss)/len(mean_loss)}")

def main():
    model = Yolov1(split_size=7, num_boxes=2, num_classes=20).to(DEVICE)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    loss_fn = YoloLoss()
    train_dataset = VOCDataset("data/train.csv", transform=transform, img_dir=IMG_DIR, label_dir=LABEL_DIR)
    test_dataset = VOCDataset("data/test.csv", transform=transform, img_dir=IMG_DIR, label_dir=LABEL_DIR)
    train_loader=DataLoader(dataset=train_dataset, batch_size=BATCH_SIZE, num_workers=1, pin_memory=PIN_MEMORY, shuffle=True,drop_last=True)
    test_loader=DataLoader(dataset=test_dataset, batch_size=BATCH_SIZE, num_workers=1, pin_memory=PIN_MEMORY, shuffle=True,drop_last=True)
    for epoch in range(EPOCHS):
        pred_boxes, target_boxes = get_bboxes(train_loader, model, iou_threshold=0.5, threshold=0.4)
        mAP = mean_average_precision(pred_boxes, target_boxes, iou_threshold=0.5)
        print(f"Train mAP:{mAP}")
        train_fn(train_loader, model, optimizer, loss_fn)
    if epoch > 99:
        for x, y in test_loader:
        x = x.to(DEVICE)
        for idx in range(16):
            bboxes = cellboxes_to_boxes(model(x))
            bboxes = non_max_suppression(bboxes[idx], iou_threshold=0.5, threshold=0.4)
            plot_image(x[idx].permute(1,2,0).to("cpu"), bboxes)
        
        

if __name__  == "__main__":
    
    main()


