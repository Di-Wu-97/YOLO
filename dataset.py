import torch
import os 
import pandas as pd
from PIL import Image

class VOCDataset(torch.utils.data.Dataset):
    def __init__(self, csv_file, img_dir, label_dir, S=7, B=2, C=20, transform=None):
        self.annotations = pd.read_csv(csv_file)
        self.img_dir = img_dir
        self.label_dir = label_dir
        self.transform = transform
        self.S=S
        self.B=B
        self.C=C
    def __len__(self):
        return len(self.annotations)

    def __getitem__(self,index):
        label_path = os.path.join(self.label_dir, self.annotations.iloc[index,1])
        boxes=[]
        with open(label_path) as f:
            for label in f.readlines():
                class_label, x, y, w, h = [
                    float(x) if float(x) != int(float(x)) else int(x) for x in label.replace("\n", "").split()
                ]

                boxes.append([class_label, x,y,w,h])
        img_path = os.path.join(self.img_dir, self.annotations.iloc[index, 0])
        image = Image.open(img_path)
        boxes = torch.tensor(boxes)

        if self.transform:
            image, boxes = self.transform(image, boxes)
        label_matrix = torch.zeros((self.S, self.S, self.C + self.B * 5)) 
        
        for box in boxes:
            class_label,x,y,w,h = box.tolist()
            class_label = int(class_label)
            i,j = int(self.S * y), int(self.S*x)  # The original x,y,w,h are crossponding to the image, multiply 7 so it matchs with each grid 
            x_cell, y_cell = self.S * x - j, self.S * y - i 
            w_cell, h_cell = w * self.S, h *self.S
            if label_matrix[i,j,20] == 0:
                label_matrix[i,j,20] = 1
                box_coord = torch.tensor([x_cell, y_cell, w_cell, h_cell])
                label_matrix[i,j, 21:25] = box_coord
                label_matrix[i, j, class_label] = 1
            
        return image, label_matrix
