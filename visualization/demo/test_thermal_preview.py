"""Portable display-only tests; no private recordings or replay artifacts."""
import base64
from types import SimpleNamespace
import cv2
import numpy as np
from thermal_preview import preview

def pixels(p):return np.frombuffer(base64.b64decode(p['pixels']),dtype=np.uint8).reshape(p['height'],p['width'],3)
source=np.array([[0,27000,41000,55000,65535]],dtype=np.uint16);original=source.copy()
p=preview(SimpleNamespace(image=source));rgb=pixels(p)
assert p['minimum']==27000 and p['maximum']==55000 and p['colormap']=='Turbo'
assert np.array_equal(rgb[0,0],rgb[0,1]) and np.array_equal(rgb[0,3],rgb[0,4])
expected=cv2.applyColorMap(np.array([[0,0,127,255,255]],dtype=np.uint8),cv2.COLORMAP_TURBO)[:,:,::-1]
assert np.array_equal(rgb,expected) and np.array_equal(source,original)
# Identical intensity has identical color even when the other pixels differ.
assert np.array_equal(pixels(preview(SimpleNamespace(image=np.array([[41000,0]],dtype=np.uint16))))[0,0],rgb[0,2])
big=np.arange(400*1280,dtype=np.uint32).reshape(400,1280).astype(np.uint16);p=preview(SimpleNamespace(image=big))
assert max(p['height'],p['width'])<=192 and p['stride']==7
idx=((np.clip(big[::7,::7].astype(np.float32),27000,55000)-27000)*255/28000).astype(np.uint8)
assert np.array_equal(pixels(p),cv2.applyColorMap(idx,cv2.COLORMAP_TURBO)[:,:,::-1])
print('PASS Turbo endpoints, fixed scale across frames, RGB order, actual sampled pixels, nonmutation and size bound')
