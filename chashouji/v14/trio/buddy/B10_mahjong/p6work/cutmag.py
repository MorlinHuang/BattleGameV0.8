import sys,numpy as np
sys.path.insert(0,'/workspace/art/chashouji/v14')
from crewart import cut
from PIL import Image
rgb,al=cut(sys.argv[1],'magenta',(40,150))
Image.fromarray(np.dstack([rgb,al*255]).clip(0,255).astype(np.uint8),'RGBA').save(sys.argv[2])
