import numpy as np
from PIL import Image
from skimage.feature import ORB, match_descriptors
from skimage.measure import ransac
from skimage.transform import AffineTransform
from scipy.ndimage import map_coordinates
from scipy.optimize import minimize
WORLD='/workspace/art/chashouji/v14/bg/v15/world.png'
def gray(a): return a[...,:3]@np.array([.299,.587,.114],np.float32)
def orb_init(tile, vid):
  o1=ORB(n_keypoints=3000,fast_threshold=0.03); o1.detect_and_extract(gray(tile)/255)
  o2=ORB(n_keypoints=3000,fast_threshold=0.03); o2.detect_and_extract(gray(vid)/255)
  m=match_descriptors(o1.descriptors,o2.descriptors,cross_check=True,max_ratio=0.85)
  src=o1.keypoints[m[:,0]][:,::-1]; dst=o2.keypoints[m[:,1]][:,::-1]  # (x,y)
  model,inl=ransac((src,dst),AffineTransform,min_samples=3,residual_threshold=3,max_trials=4000,rng=0)
  return model,inl.sum(),len(m)
def refine(tile, vid, p0, ring):
  """p=(a,b,c,d): u=a*x+b, v=c*y+d. ring: bool mask in tile coords. normalized-gray L1."""
  tg=gray(tile); vg=gray(vid)
  ys,xs=np.nonzero(ring)
  if len(ys)>40000: sel=np.random.default_rng(0).choice(len(ys),40000,replace=False); ys,xs=ys[sel],xs[sel]
  t=tg[ys,xs]; t=(t-t.mean())/t.std()
  def err(p):
    v=map_coordinates(vg,[p[2]*ys+p[3],p[0]*xs+p[1]],order=1,mode='nearest'); v=(v-v.mean())/(v.std()+1e-6)
    return np.abs(v-t).mean()
  r=minimize(err,p0,method='Powell',options={'xtol':1e-4,'ftol':1e-5,'maxiter':4000})
  return r.x, err(p0), r.fun
def load_tile(x0): return np.asarray(Image.open(WORLD).convert('RGB').crop((x0,0,x0+960,1707))).astype(np.float32)
def load(f): return np.asarray(Image.open(f).convert('RGB')).astype(np.float32)
