#!/usr/bin/env python3
"""Fast x4 upscaler for video frames: Real-ESRGAN "realesr-general-x4v3" (SRVGGNetCompact), CPU.

    python3 fast_sr.py WEIGHTS IN_DIR OUT_DIR [--blend 0.2]

Every PNG in IN_DIR is upscaled x4 and written to OUT_DIR (skips files already done). A small Lanczos blend keeps
grain natural so faces don't look plastic.
"""
import os
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image


class SRVGGNetCompact(nn.Module):
    def __init__(self, num_feat=64, num_conv=32, upscale=4):
        super().__init__()
        self.upscale = upscale
        body = [nn.Conv2d(3, num_feat, 3, 1, 1), nn.PReLU(num_parameters=num_feat)]
        for _ in range(num_conv):
            body += [nn.Conv2d(num_feat, num_feat, 3, 1, 1), nn.PReLU(num_parameters=num_feat)]
        body += [nn.Conv2d(num_feat, 3 * upscale * upscale, 3, 1, 1)]
        self.body = nn.ModuleList(body)
        self.upsampler = nn.PixelShuffle(upscale)

    def forward(self, x):
        out = x
        for m in self.body:
            out = m(out)
        out = self.upsampler(out)
        return out + F.interpolate(x, scale_factor=self.upscale, mode="nearest")


def main():
    weights, src, dst = sys.argv[1:4]
    blend = float(sys.argv[sys.argv.index("--blend") + 1]) if "--blend" in sys.argv else 0.2
    torch.set_num_threads(os.cpu_count())
    net = SRVGGNetCompact()
    sd = torch.load(weights, map_location="cpu")
    net.load_state_dict(sd.get("params", sd))
    net.eval()
    os.makedirs(dst, exist_ok=True)
    names = sorted(n for n in os.listdir(src) if n.endswith(".png"))
    for k, n in enumerate(names):
        out = os.path.join(dst, n)
        if os.path.exists(out):
            continue
        im = Image.open(os.path.join(src, n)).convert("RGB")
        x = torch.from_numpy(np.asarray(im, np.float32) / 255).permute(2, 0, 1)[None]
        with torch.no_grad():
            y = net(x).clamp(0, 1)[0].permute(1, 2, 0).numpy() * 255
        up = Image.fromarray(y.astype(np.uint8))
        if blend:
            lz = np.asarray(im.resize(up.size, Image.LANCZOS), np.float32)
            up = Image.fromarray((np.asarray(up, np.float32) * (1 - blend) + lz * blend).astype(np.uint8))
        up.save(out)
        if k % 25 == 0:
            print(f"{k}/{len(names)}", flush=True)
    print("SR_DONE", dst)


if __name__ == "__main__":
    main()
