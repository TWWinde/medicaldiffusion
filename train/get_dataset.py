from dataset import MRNetDataset, BRATSDataset, ADNIDataset, DUKEDataset, LIDCDataset, DEFAULTDataset, SynthRAD2023Dataset, AutoPETDataset, SemanticMapDataset, TotalSegmentator_mri_Dataset
from torch.utils.data import WeightedRandomSampler


def get_dataset(cfg):
    print("Model is trained on ", cfg.dataset.name)
    if cfg.dataset.name == 'MRNet':
        train_dataset = MRNetDataset(
            root_dir=cfg.dataset.root_dir, task=cfg.dataset.task, plane=cfg.dataset.plane, split='train')
        val_dataset = MRNetDataset(root_dir=cfg.dataset.root_dir,
                                   task=cfg.dataset.task, plane=cfg.dataset.plane, split='valid')
        sampler = WeightedRandomSampler(
            weights=train_dataset.sample_weight, num_samples=len(train_dataset.sample_weight))
        return train_dataset, val_dataset, sampler
    if cfg.dataset.name == 'BRATS':
        train_dataset = BRATSDataset(
            root_dir=cfg.dataset.root_dir, imgtype=cfg.dataset.imgtype, train=True, severity=cfg.dataset.severity, resize=cfg.dataset.resize)
        val_dataset = BRATSDataset(
            root_dir=cfg.dataset.root_dir, imgtype=cfg.dataset.imgtype, train=True, severity=cfg.dataset.severity, resize=cfg.dataset.resize)
        sampler = None
        return train_dataset, val_dataset, sampler
    if cfg.dataset.name == 'ADNI':
        train_dataset = ADNIDataset(
            root_dir=cfg.dataset.root_dir, augmentation=True)
        val_dataset = ADNIDataset(
            root_dir=cfg.dataset.root_dir, augmentation=True)
        sampler = None
        return train_dataset, val_dataset, sampler
    if cfg.dataset.name == 'DUKE':
        if cfg.model.name == 'vq_gan_3d':
            train_dataset = DUKEDataset(
                root_dir=cfg.dataset.root_dir)
            val_dataset = DUKEDataset(
                root_dir=cfg.dataset.val_dir)
            sampler = None
            return train_dataset, val_dataset, sampler
        elif cfg.model.name == 'ddpm' or 'vq_gan_spade':
            train_dataset = DUKEDataset(
                root_dir=cfg.dataset.root_dir, sem_map=True)
            val_dataset = DUKEDataset(
                root_dir=cfg.dataset.val_dir, sem_map=True)
            sampler = None
            return train_dataset, val_dataset, sampler
    if cfg.dataset.name == 'LIDC':
        train_dataset = LIDCDataset(
            root_dir=cfg.dataset.root_dir, augmentation=True)
        val_dataset = LIDCDataset(
            root_dir=cfg.dataset.root_dir, augmentation=True)
        sampler = None
        return train_dataset, val_dataset, sampler
    if cfg.dataset.name == 'DEFAULT':
        train_dataset = DEFAULTDataset(
            root_dir=cfg.dataset.root_dir)
        val_dataset = DEFAULTDataset(
            root_dir=cfg.dataset.root_dir)
        sampler = None

    if cfg.dataset.name == 'SemanticMap':
        train_dataset = SemanticMapDataset(
            root_dir=cfg.dataset.root_dir, )
        val_dataset = SemanticMapDataset(
            root_dir=cfg.dataset.val_dir, )
        sampler = None
        return train_dataset, val_dataset, sampler

    if cfg.dataset.name == 'SynthRAD2023':
        if cfg.model.name == 'vq_gan_3d':
            train_dataset = SynthRAD2023Dataset(
                root_dir=cfg.dataset.root_dir)
            val_dataset = SynthRAD2023Dataset(
                root_dir=cfg.dataset.val_dir)
            sampler = None
            return train_dataset, val_dataset, sampler
        elif cfg.model.name == 'ddpm' or 'vq_gan_spade':
            train_dataset = SynthRAD2023Dataset(
                root_dir=cfg.dataset.root_dir, sem_map=True)
            val_dataset = SynthRAD2023Dataset(
                root_dir=cfg.dataset.val_dir, sem_map=True)
            sampler = None
            return train_dataset, val_dataset, sampler

    if cfg.dataset.name == 'SynthRAD2023_wo_mask':
        if cfg.model.name == 'vq_gan_3d':
            train_dataset = SynthRAD2023Dataset(
                root_dir=cfg.dataset.root_dir)
            val_dataset = SynthRAD2023Dataset(
                root_dir=cfg.dataset.val_dir)
            sampler = None
            return train_dataset, val_dataset, sampler
        elif cfg.model.name == 'ddpm':
            train_dataset = SynthRAD2023Dataset(
                root_dir=cfg.dataset.root_dir, sem_map=True)
            val_dataset = SynthRAD2023Dataset(
                root_dir=cfg.dataset.root_dir, sem_map=True)
            sampler = None
            return train_dataset, val_dataset, sampler

    if cfg.dataset.name == 'AutoPET':
        if cfg.model.name == 'vq_gan_3d':
            train_dataset = AutoPETDataset(
                root_dir=cfg.dataset.root_dir)
            val_dataset = AutoPETDataset(
                root_dir=cfg.dataset.val_dir)
            sampler = None
            return train_dataset, val_dataset, sampler
        elif cfg.model.name == 'ddpm' or 'vq_gan_spade':
            train_dataset = AutoPETDataset(
                root_dir=cfg.dataset.root_dir, sem_map=True)
            val_dataset = AutoPETDataset(
                root_dir=cfg.dataset.val_dir, sem_map=True)
            sampler = None
            return train_dataset, val_dataset, sampler

    if cfg.dataset.name == 'TotalSegmentator_mri':

        if cfg.model.name == 'vq_gan_3d':
            train_dataset = TotalSegmentator_mri_Dataset(
                root_dir=cfg.dataset.root_dir)
            val_dataset = SynthRAD2023Dataset(
                root_dir=cfg.dataset.val_dir)
            sampler = None
            return train_dataset, val_dataset, sampler
        elif cfg.model.name == 'ddpm' or 'vq_gan_spade':
            train_dataset = TotalSegmentator_mri_Dataset(
                root_dir=cfg.dataset.root_dir, sem_map=True)
            val_dataset = TotalSegmentator_mri_Dataset(
                root_dir=cfg.dataset.val_dir, sem_map=True)
            sampler = None
            return train_dataset, val_dataset, sampler

    raise ValueError(f'{cfg.dataset.name} Dataset is not available')
