# 用法: pick.sh 上一帧 候选1 候选2 ...  —— 淘汰黑底候选、报对齐后差异、拼一张对比图 /tmp/pick.jpg
prev=$1; shift
python3 - "$prev" "$@" <<'PY'
import sys, numpy as np
from PIL import Image
fs=sys.argv[1:]
for f in fs[1:]:
    x=np.array(Image.open(f).convert('RGB').resize((256,171))).astype(int)
    mag=((x[...,0]>200)&(x[...,2]>200)&(x[...,1]<80)).mean()
    print(f[-7:], '品红底占比 %.0f%%'%(mag*100), '<-- 黑底淘汰' if mag<0.3 else '')
o=Image.new('RGB',(614*len(fs),410))
for i,f in enumerate(fs): o.paste(Image.open(f).convert('RGB').resize((614,410)),(614*i,0))
o.save('/tmp/pick.jpg',quality=80)
PY
python3 "$(dirname $0)/reg.py" "$prev" "$@"
