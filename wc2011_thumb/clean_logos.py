"""Remove jersey sponsor logos (Sahara, Nike, Dilmah, MAS, sleeve badges) by inpainting -> clean/<name>.png"""
import cv2
import numpy as np

BOXES = {
    "sehwag": [(522, 336, 618, 366), (533, 311, 561, 326)],
    "murali": [(190, 198, 293, 253), (141, 236, 170, 284), (303, 106, 336, 128)],
}
for name in ["sehwag", "murali", "sachin", "dhoni", "yuvraj"]:
    im = cv2.imread(f"src/{name}.jpg")
    m = np.zeros(im.shape[:2], np.uint8)
    for x0, y0, x1, y1 in BOXES.get(name, []):
        m[y0:y1, x0:x1] = 255
    if m.any():
        im = cv2.inpaint(im, cv2.dilate(m, np.ones((5, 5), np.uint8)), 9, cv2.INPAINT_TELEA)
    cv2.imwrite(f"clean/{name}.png", im)
