import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
import torchio as tio
import os
import nibabel as nib
import random
from torchvision import transforms as TR


def preprocess_input(opt, data, test=False):
    data['label'] = data['label'].long()
    if opt.gpu_ids != "-1":
        data['label'] = data['label'].cuda()
        if not test:
            data['image'] = data['image'].cuda()
        else:
            data['image'] = data['image'].cuda()
            data['ct_image'] = data['ct_image'].cuda()
    label_map = data['label']
    bs, _, h, w = label_map.size()
    nc = opt.semantic_nc
    if opt.gpu_ids != "-1":
        input_label = torch.cuda.FloatTensor(bs, nc, h, w).zero_()
    else:
        input_label = torch.FloatTensor(bs, nc, h, w).zero_()
    input_semantics = input_label.scatter_(1, label_map, 1.0)
    if test:
        return data['image'], data['ct_image'], input_semantics
    else:
        return data['image'], input_semantics



class Transform:
    def __init__(self, target_depth=32, label=False):
        self.target_depth = target_depth
        self.label = label

    def normalization(self, data):
        arr_min = data.min()
        arr_max = data.max()
        data_normalized = (data - arr_min) / (arr_max - arr_min)
        data_normalized = data_normalized * 2 - 1
        return data_normalized

    def randomdepthcrop(self, img, seg=None):
        h, w, d = img.shape

        if self.label:
            assert img.shape == seg.shape
            target_d = self.target_depth

            d_start = np.random.randint(2, d - target_d + 1)
            cropped_img = img[:, :, d_start:d_start + target_d]
            cropped_seg = seg[:, :, d_start:d_start + target_d]

            return cropped_img, cropped_seg
        else:
            target_d = self.target_depth

            d_start = np.random.randint(0, d - target_d + 1)
            cropped_img = img[:, :, d_start:d_start + target_d]

            return cropped_img

    def pad_and_concatenate_image(self, array):

        c, a, b = array.shape[0], array.shape[1], array.shape[2]

        max_length = max(a, b)

        if a < max_length:
            pad1 = np.tile(array[:, 0:1, :], (1, (max_length - a) // 2, 1))
            pad2 = np.tile(array[:, -1:, :], (1, (max_length - a) - (max_length - a) // 2, 1))
            padded_array = np.concatenate((pad1, array, pad2), axis=1)
        else:
            padded_array = array

        if b < max_length:
            pad1 = np.tile(padded_array[:, :, 0:1], (1, 1, (max_length - b) // 2))
            pad2 = np.tile(padded_array[:, :, -1:], (1, 1, (max_length - b) - (max_length - b) // 2))
            padded_array = np.concatenate((pad1, padded_array, pad2), axis=2)

        return padded_array

    def __call__(self, img, seg=None):
        if self.label:
            img, seg = self.randomdepthcrop(img, seg)
            final_img = self.normalization(img)

            return final_img, seg
        else:
            img = self.randomdepthcrop(img)
            final_img = self.normalization(img)

            return final_img


class SynthRAD2023Dataset(Dataset):
    def __init__(self, root_dir: str, sem_map=False):
        super().__init__()
        self.root_dir = root_dir
        self.sem_map = sem_map
        if self.sem_map:
            self.transform = Transform(target_depth=32, label=True)
            self.mr_paths, self.label_paths = self.get_data_files()
        else:
            self.transform = Transform(target_depth=32, label=False)
            self.mr_paths = self.get_data_files()

    def get_data_files(self):
        if self.sem_map:
            mr_names, label_names = [], []
            subfolder_names = os.listdir(self.root_dir)
            for item in subfolder_names:
                mr_path = os.path.join(self.root_dir, item, 'mr.nii.gz')
                label_path = os.path.join(self.root_dir, item, 'label.nii.gz')
                if os.path.exists(mr_path) and os.path.exists(label_path):
                    mr_names.append(mr_path)
                    label_names.append(label_path)

            return mr_names, label_names
        else:
            subfolder_names = os.listdir(self.root_dir)
            mr_names = [os.path.join(self.root_dir, subfolder, 'mr.nii.gz') for subfolder in subfolder_names
                        if os.path.exists(os.path.join(self.root_dir, subfolder, 'mr.nii.gz'))]

            return mr_names

    def __len__(self):
        return len(self.mr_paths)

    def resize(self, img, label=None):

        if self.sem_map:
            assert img.shape == label.shape
            torch.nn.functional.interpolate(img, size=(32, 256, 256), mode='bilinear', align_corners=False)

            return img, label

        else:
            torch.nn.functional.interpolate(img, size=(32, 256, 256), mode='bilinear', align_corners=False)

            return img

    def __getitem__(self, idx: int):
        if self.sem_map:
            img = nib.load(self.mr_paths[idx])
            label = nib.load(self.label_paths[idx])
            img = img.get_fdata()
            label = label.get_fdata()
            img, label = self.transform(img, label)
            img = torch.from_numpy(img).unsqueeze(0).float().permute(0, -1, 1, 2)
            label = torch.from_numpy(label).unsqueeze(0).float().permute(0, -1, 1, 2)
            if random.random() < 0.5:
                img = TR.functional.hflip(img)
                label = TR.functional.hflip(label)
            if random.random() < 0.5:
                angle = random.choice([90, 180, 270])
                img = TR.functional.rotate(img, angle)
                label = TR.functional.rotate(label, angle)

            return {'image': img, 'label': label}
        else:
            img = nib.load(self.mr_paths[idx])
            img = img.get_fdata()
            img = self.transform(img)
            img = torch.from_numpy(img).unsqueeze(0).float().permute(0, -1, 1, 2)

            if random.random() < 0.5:
                img = TR.functional.hflip(img)
            if random.random() < 0.5:
                angle = random.choice([90, 180, 270])
                img = TR.functional.rotate(img, angle)

            return {'image': img}


if __name__ == '__main__':
    #dataset = MRDataset(root_dir='/Users/tangwenwu/Desktop/Master_thesis/data/dataset', sem_map=True)
    dataset = SynthRAD2023Dataset(root_dir='/Users/tangwenwu/Desktop/Master_thesis/data/dataset')
    dataloader = DataLoader(dataset, batch_size=1, shuffle=True, num_workers=2)
    for i, data in enumerate(dataloader):
        print(f"Batch {i + 1}:")
        #print("Image shape:", data['image'].shape)
        #print("Label shape:", data['label'].shape)
        print("Label shape:", data['data'].shape)

