# FocusCodec — project conventions

AI-guided region-of-interest (ROI) video coding for low-bandwidth video calls. Personal context, if present, is in `CLAUDE.local.md` (git-ignored).

## Pipeline
1. Person segmentation (DeepLabV3 baseline, then a U-Net on a pretrained encoder).
2. Per-frame ΔQP map on the 64×64 CTU grid (dilation, EMA + hysteresis smoothing).
3. Encode with Kvazaar `--roi`.
4. Compare against a no-ROI baseline at QP {27, 32, 37, 42}: PSNR/SSIM (full | ROI | background), VMAF, BD-rate.

**Cloud track (AWS, Terraform in `infra/`):**
- One Docker image (PyTorch CPU + Kvazaar + FFmpeg) in ECR.
- S3 upload → EventBridge → Step Functions:
  1. segment on Fargate
  2. Map of encode + evaluate tasks on Fargate
  3. aggregate Lambda
- Results go to S3 + DynamoDB.
- Demo on S3 + CloudFront (OAC).
- API Gateway + Lambda for presigned uploads and job status.
- GitHub Actions with OIDC.

**Cloud rules:**
- Never create AWS resources outside Terraform. Confirm before any `terraform apply` or `destroy`.
- No NAT Gateway, no load balancer. A budget alarm must exist before anything else.
- Model training happens off AWS (Colab); AWS runs CPU inference only.
- Keep raw videos, weights and other large artifacts out of git.

## Commands
- `make setup`: venv + package
- `make test`: pytest
- `make smoke`: Kvazaar per-frame ROI check
- `make videos`: fetch Xiph clips into `data/`

## Git workflow
- **One logical change per commit**, with tests passing.
- **Branches:** `main` only receives merges. Work on `feat/<topic>`, `fix/<topic>`, `chore/<topic>`, `docs/<topic>`, `test/<topic>`, `ci/<topic>` or `infra/<topic>`, and merge through a pull request.
- **Before every commit, PR or merge**, show the branch, the files changed, a plain summary of what changes and which feature it adds, and the proposed message. Proceed only after approval.
- **Message format: Conventional Commits + the 7 rules of a good commit message.**
  1. Separate subject from body with a blank line.
  2. Limit the subject line to 50 characters, including the `type(scope): ` prefix.
  3. Capitalize the description after the prefix: `feat(roi): Add ...`.
  4. Do not end the subject with a period.
  5. Use the imperative mood ("Add", not "Added" or "Adds").
  6. Wrap the body at 72 characters.
  7. Use the body to explain what and why, not how.
- **Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `ci`, `chore`, `style`.
- **Scopes:** `roi`, `metrics`, `bdrate`, `video`, `seg`, `encode`, `eval`, `web`, `infra`, `ci`, `scripts`.
- **Breaking changes:** add `!` after the type and a `BREAKING CHANGE:` footer.
