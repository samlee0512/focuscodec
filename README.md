# FocusCodec

**AI-guided region-of-interest video coding for low-bandwidth video calls.**
A segmentation network finds the people in each frame. The HEVC encoder ([Kvazaar](https://github.com/ultravideo/kvazaar)) then spends more bits on them and fewer on the background.

The pipeline also runs as a serverless AWS workflow (Terraform, ECS Fargate, Step Functions, S3, CloudFront), so experiments fan out in parallel.

> Status: early development. Results will appear here.

## Question
At equal bitrate:
- How much better do people look (ROI-PSNR/SSIM)?
- What does the background, and full-frame VMAF, lose?
- Is segmentation fast enough for live calls?

## Pipeline
```
video ─► segment (DeepLabV3 baseline → U-Net) ─► person masks
masks ─► roi_map (CTU grid, dilation, temporal smoothing) ─► per-frame ΔQP ─► roi.bin
video + roi.bin ─► kvazaar --qp Q --roi roi.bin ─► .hevc   (baseline: no --roi)
.hevc ─► decode ─► PSNR/SSIM (full | ROI | background), VMAF, bitrate ─► BD-rate
```

## Quick start
```bash
brew install kvazaar ffmpeg
make setup      # venv + package
make test       # unit tests
make smoke      # checks Kvazaar applies per-frame ROI maps
make videos     # fetch Xiph test sequences into data/
```

## Related work
Foveated image/video communication (A. Basu et al., University of Alberta); ROI coding in HEVC. *(citations to be added)*
