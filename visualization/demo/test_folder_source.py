"""Temporary ingestion fixtures; no research artifacts are modified."""
import struct,tempfile
from pathlib import Path
from folder_source import FolderSimulationSource,ready_payload,Pending

class Clock:
    t=0
    def __call__(self):return self.t
    def tick(self,s):self.t+=.3;s.poll()
def payload():return struct.pack('<HHHH',4,4,8,0)+bytes([0]*16)
def put(d,i,body=None):
    p=d/f'Image{i:06d}.dat';p.write_bytes(payload() if body is None else body);return p
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);code=root/'test.mpf';code.write_text('not parsed for thermal inference')
    def source(name,first=None):
        d=root/name;d.mkdir();c=Clock();s=FolderSimulationSource(d,code,first_index=first,clock=c);return d,c,s
    d,c,s=source('empty');c.tick(s);assert s.cursor==0 and s.lifecycle=='WAITING FOR DATA' and s.stage=='AWAITING REPLAY'
    put(d,2);put(d,1);c.tick(s);assert s.cursor==0;c.tick(s);assert s.cursor==2 and s.latest['filename']=='Image000002.dat'
    c.tick(s);assert s.cursor==2
    put(d,4);c.tick(s);assert s.cursor==2 and s.lifecycle=='DATA QUALITY ISSUE'
    put(d,3);c.tick(s);c.tick(s);assert s.cursor==4
    s.stop();put(d,5);c.tick(s);assert s.cursor==4 and s.lifecycle=='STOPPED'
    try:s.reset();raise AssertionError()
    except ValueError:pass
    d,c,s=source('incomplete',1);p=put(d,1,payload()[:10]);c.tick(s);c.tick(s);assert s.cursor==0 and not s.error
    p.write_bytes(payload());c.tick(s);c.tick(s);assert s.cursor==1
    d,c,s=source('malformed');put(d,1,struct.pack('<HHHH',4,4,16,0)+bytes(32));c.tick(s);c.tick(s);assert s.error and s.cursor==0
    d,c,s=source('late');put(d,10);c.tick(s);c.tick(s);put(d,9);c.tick(s);assert s.error and s.cursor==1
    d,c,s=source('duplicate');put(d,1);(d/'Image1.dat').write_bytes(payload());c.tick(s);assert s.error
    d,c,s=source('mutated');p=put(d,1);c.tick(s);c.tick(s);p.write_bytes(payload()+b'x');c.tick(s);assert s.error
    d,c,s=source('existing');put(d,7);c.tick(s);c.tick(s);assert s.cursor==1
    snapshot=s.snapshot();assert snapshot['mode']=='Folder Simulation' and snapshot['total_frames'] is None and len(snapshot['history'])==1
    # Altering selected G-code contents cannot influence any thermal field.
    d2=root/'alternate';d2.mkdir();put(d2,7);code.write_text('M30 completely different config')
    c2=Clock();s2=FolderSimulationSource(d2,code,clock=c2);c2.tick(s2);c2.tick(s2)
    for k in ('current','history','inspections','stage','evidence'):assert s.snapshot()[k]==s2.snapshot()[k],k
print('PASS empty, real pipeline fixtures, batch order, exactly-once, gap recovery, incomplete retry, malformed/duplicate/late/modified, stop, existing, config isolation')
# Causal implementation parity against the frozen replay trace; metrics only, no labels.
import json,csv
from causal_events import Replay
from replay_source import FEATURES,TRACE
if FEATURES is None or TRACE is None:
 print('SKIP optional private replay parity: configure replay artifact paths')
 raise SystemExit(0)
engine=Replay();actual=[]
with FEATURES.open() as f:
 for r in csv.DictReader(f):
  if int(r['frame'])>1750:break
  row={'frame':int(r['frame']),'classification':r['classification'],**{k:float(r[k]) for k in ('area_px','aspect_ratio','circularity','band3')}}
  engine.update(row);actual+=engine.trace;engine.trace=[]
expected=[json.loads(line) for line in TRACE.open() if json.loads(line)['decision_frame']<=1750]
assert actual==expected
print('PASS demo-local causal engine parity for1750 stored frames, no raw processing')
