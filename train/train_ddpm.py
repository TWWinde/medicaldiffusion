import sys

sys.path.append('/misc/no_backups/d1502/medicaldiffusion')
from ddpm import Unet3D, GaussianDiffusion, Trainer, Unet3D_SPADE, SemanticGaussianDiffusion, Semantic_Trainer
import hydra
from omegaconf import DictConfig, open_dict
from train.get_dataset import get_dataset
import torch
import os
from ddpm.unet import UNet


# NCCL_P2P_DISABLE=1 accelerate launch train/train_ddpm.py

@hydra.main(config_path='/misc/no_backups/d1502/medicaldiffusion/config', config_name='base_cfg', version_base=None)
def run(cfg: DictConfig):
    torch.cuda.set_device(cfg.model.gpus)
    with open_dict(cfg):
        cfg.model.results_folder = os.path.join(
            cfg.model.results_folder, cfg.dataset.name, cfg.model.results_folder_postfix)
    print("Task name:", cfg.model.results_folder_postfix, cfg.model.denoising_fn, "and", cfg.model.diffusion, 'are implemented')
    if cfg.model.denoising_fn == 'Unet3D':
        model = Unet3D(
            dim=cfg.model.diffusion_img_size,
            dim_mults=cfg.model.dim_mults,
            channels=cfg.model.diffusion_num_channels,
        ).cuda()
    elif cfg.model.denoising_fn == 'Unet3D_SPADE':
        model = Unet3D_SPADE(
            dim=cfg.model.diffusion_img_size,
            dim_mults=cfg.model.dim_mults,
            channels=cfg.model.diffusion_num_channels,
            label_nc=cfg.dataset.label_nc,
            spade_input_nc=cfg.model.spade_input_channel if cfg.model.segconv != 0 else None,
            segconv=False if cfg.model.segconv == 0 else True,
            vqvae=False if cfg.model.vqvae_ckpt == 0 else cfg.model.vqvae_ckpt,
            add_seg_to_noise=False if cfg.model.add_seg_to_noise == 0 else True,
        ).cuda()
    elif cfg.model.denoising_fn == 'UNet':
        model = UNet(
            in_ch=cfg.model.diffusion_num_channels,
            out_ch=cfg.model.diffusion_num_channels,
            spatial_dims=3
        ).cuda()
    else:
        raise ValueError(f"Model {cfg.model.denoising_fn} doesn't exist")

    if cfg.model.diffusion == 'SemanticGaussianDiffusion':
        diffusion = SemanticGaussianDiffusion(
            cfg,
            model,
            vqgan_ckpt=None if cfg.model.vqgan_ckpt == 0 else cfg.model.vqgan_ckpt,
            vqgan_spade_ckpt=None if cfg.model.vqgan_spade_ckpt == 0 else cfg.model.vqgan_spade_ckpt,
            vqvae_ckpt=None if cfg.model.vqvae_ckpt == 0 else cfg.model.vqgvae_ckpt,
            image_size=cfg.model.diffusion_img_size,
            num_frames=cfg.model.diffusion_depth_size,
            channels=cfg.model.diffusion_num_channels,
            timesteps=cfg.model.timesteps,
            # sampling_timesteps=cfg.model.sampling_timesteps,
            loss_type=cfg.model.loss_type,
            cond_scale=cfg.model.cond_scale,
            # objective=cfg.objective
            add_seg_to_noise=False if cfg.model.add_seg_to_noise == 0 else True,
        ).cuda()
    elif cfg.model.diffusion == 'GaussianDiffusion':
        diffusion = GaussianDiffusion(
            model,
            vqgan_ckpt=cfg.model.vqgan_ckpt,
            image_size=cfg.model.diffusion_img_size,
            num_frames=cfg.model.diffusion_depth_size,
            channels=cfg.model.diffusion_num_channels,
            timesteps=cfg.model.timesteps,
            # sampling_timesteps=cfg.model.sampling_timesteps,
            loss_type=cfg.model.loss_type,
            # objective=cfg.objective
        ).cuda()
    else:
        raise ValueError(f"Model {cfg.model.diffusion} doesn't exist")

    train_dataset, val_dataset, _ = get_dataset(cfg)

    if cfg.model.diffusion == 'SemanticGaussianDiffusion':
        trainer = Semantic_Trainer(
            diffusion,
            cfg=cfg,
            train_dataset=train_dataset,
            val_dataset=val_dataset,
            train_batch_size=cfg.model.batch_size,
            save_and_sample_every=cfg.model.save_and_sample_every,
            train_lr=cfg.model.train_lr,
            train_num_steps=cfg.model.train_num_steps,
            gradient_accumulate_every=cfg.model.gradient_accumulate_every,
            ema_decay=cfg.model.ema_decay,
            amp=cfg.model.amp,
            num_sample_rows=cfg.model.num_sample_rows,
            results_folder=cfg.model.results_folder,
            num_workers=cfg.model.num_workers,
            vqvae_ckpt=None if cfg.model.vqvae_ckpt == 0 else cfg.model.vqvae_ckpt,
            # logger=cfg.model.logger
            vqgan_spade_ckpt=None if cfg.model.vqgan_spade_ckpt == 0 else True
        )

    elif cfg.model.diffusion == 'GaussianDiffusion':
        trainer = Trainer(
            diffusion,
            cfg=cfg,
            dataset=train_dataset,
            train_batch_size=cfg.model.batch_size,
            save_and_sample_every=cfg.model.save_and_sample_every,
            train_lr=cfg.model.train_lr,
            train_num_steps=cfg.model.train_num_steps,
            gradient_accumulate_every=cfg.model.gradient_accumulate_every,
            ema_decay=cfg.model.ema_decay,
            amp=cfg.model.amp,
            num_sample_rows=cfg.model.num_sample_rows,
            results_folder=cfg.model.results_folder,
            num_workers=cfg.model.num_workers,
            # logger=cfg.model.logger
        )

    else:
        raise ValueError(f"Model {cfg.model.diffusion} doesn't exist")

    if cfg.model.load_milestone == -1:
        trainer.load(cfg.model.load_milestone)

    trainer.train()


if __name__ == '__main__':
    run()

    # wandb.finish()
    # Incorporate GAN loss in DDPM training?
    # Incorporate GAN loss in UNET segmentation?
    # Maybe better if I don't use ema updates?
    # Use with other vqgan latent space (the one with more channels?)
