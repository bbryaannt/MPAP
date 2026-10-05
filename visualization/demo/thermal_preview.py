"""Display-only sampled Turbo intensity preview; fixed window, no temperature calibration."""
import base64
import math
import cv2
import numpy as np

def preview(decoded):
    image=decoded.image
    stride=max(1,math.ceil(max(image.shape)/192))
    sampled=image[::stride,::stride]
    minimum,maximum=27000,55000
    indices=((np.clip(sampled.astype(np.float32),minimum,maximum)-minimum)*(255/(maximum-minimum))).astype(np.uint8)
    # OpenCV is already required by MPAP. Convert its BGR Turbo output to RGB.
    rgb=cv2.applyColorMap(indices,cv2.COLORMAP_TURBO)[:,:,::-1].copy()
    return dict(width=rgb.shape[1],height=rgb.shape[0],stride=stride,minimum=minimum,maximum=maximum,channels=3,colormap='Turbo',
                pixels=base64.b64encode(rgb.tobytes()).decode('ascii'))
