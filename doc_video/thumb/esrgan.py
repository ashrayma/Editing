"""Minimal Real-ESRGAN x4plus (RRDBNet) inference on CPU. usage: esrgan.py weights in out"""
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image


class RDB(nn.Module):
    def __init__(s, nf=64, gc=32):
        super().__init__()
        s.conv1 = nn.Conv2d(nf, gc, 3, 1, 1)
        s.conv2 = nn.Conv2d(nf + gc, gc, 3, 1, 1)
        s.conv3 = nn.Conv2d(nf + 2 * gc, gc, 3, 1, 1)
        s.conv4 = nn.Conv2d(nf + 3 * gc, gc, 3, 1, 1)
        s.conv5 = nn.Conv2d(nf + 4 * gc, nf, 3, 1, 1)
        s.l = nn.LeakyReLU(0.2, True)

    def forward(s, x):
        x1 = s.l(s.conv1(x))
        x2 = s.l(s.conv2(torch.cat((x, x1), 1)))
        x3 = s.l(s.conv3(torch.cat((x, x1, x2), 1)))
        x4 = s.l(s.conv4(torch.cat((x, x1, x2, x3), 1)))
        return s.conv5(torch.cat((x, x1, x2, x3, x4), 1)) * 0.2 + x


class RRDB(nn.Module):
    def __init__(s, nf=64):
        super().__init__()
        s.rdb1, s.rdb2, s.rdb3 = RDB(nf), RDB(nf), RDB(nf)

    def forward(s, x):
        return s.rdb3(s.rdb2(s.rdb1(x))) * 0.2 + x


class RRDBNet(nn.Module):
    def __init__(s, nf=64, nb=23):
        super().__init__()
        s.conv_first = nn.Conv2d(3, nf, 3, 1, 1)
        s.body = nn.Sequential(*[RRDB(nf) for _ in range(nb)])
        s.conv_body = nn.Conv2d(nf, nf, 3, 1, 1)
        s.conv_up1 = nn.Conv2d(nf, nf, 3, 1, 1)
        s.conv_up2 = nn.Conv2d(nf, nf, 3, 1, 1)
        s.conv_hr = nn.Conv2d(nf, nf, 3, 1, 1)
        s.conv_last = nn.Conv2d(nf, 3, 3, 1, 1)
        s.l = nn.LeakyReLU(0.2, True)

    def forward(s, x):
        f = s.conv_first(x)
        f = f + s.conv_body(s.body(f))
        f = s.l(s.conv_up1(F.interpolate(f, scale_factor=2, mode="nearest")))
        f = s.l(s.conv_up2(F.interpolate(f, scale_factor=2, mode="nearest")))
        return s.conv_last(s.l(s.conv_hr(f)))


net = RRDBNet()
sd = torch.load(sys.argv[1], map_location="cpu", weights_only=True)  # tensors only, no pickled code
net.load_state_dict(sd.get("params_ema", sd))
net.eval()

im = np.asarray(Image.open(sys.argv[2]).convert("RGB")).astype(np.float32) / 255
x = torch.from_numpy(im).permute(2, 0, 1)[None]
T, P = 200, 16  # tile size + overlap
_, _, h, w = x.shape
out = torch.zeros(1, 3, h * 4, w * 4)
with torch.no_grad():
    for y0 in range(0, h, T):
        for x0 in range(0, w, T):
            ya, xa = max(0, y0 - P), max(0, x0 - P)
            yb, xb = min(h, y0 + T + P), min(w, x0 + T + P)
            o = net(x[:, :, ya:yb, xa:xb])
            ty, tx = (y0 - ya) * 4, (x0 - xa) * 4
            hh, ww = (min(h, y0 + T) - y0) * 4, (min(w, x0 + T) - x0) * 4
            out[:, :, y0 * 4:y0 * 4 + hh, x0 * 4:x0 * 4 + ww] = o[:, :, ty:ty + hh, tx:tx + ww]
Image.fromarray((out[0].permute(1, 2, 0).clamp(0, 1).numpy() * 255).round().astype(np.uint8)).save(sys.argv[3])
print("ok", sys.argv[3], out.shape[-1], out.shape[-2])
