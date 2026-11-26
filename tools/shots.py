import sys, glob, os
from PIL import Image
for f in sys.argv[1:]:
    for p in glob.glob(f):
        Image.open(p).resize((512,448), Image.NEAREST).save(p[:-4]+'.png'); os.remove(p)
