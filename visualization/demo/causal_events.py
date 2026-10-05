"""Demo-local prefix accumulator; mirrors frozen ten-frame evidence definitions.
No inference/classification policy. Trace is drained after each input.
"""
from collections import deque
import numpy as np
METRICS=('area_px','aspect_ratio','circularity','band3')
def stats(rows):
 out={'n':len(rows)}
 for key in METRICS:
  a=np.array([r[key] for r in rows],float)
  out[key+'_mean']=float(a.mean()) if len(a) else None
  out[key+'_std']=float(a.std()) if len(a) else None
  out[key+'_slope']=float(np.dot(np.arange(len(a))-(len(a)-1)/2,a-a.mean())/np.sum((np.arange(len(a))-(len(a)-1)/2)**2)) if len(a)>1 else None
 return out
class Replay:
 """Receives one current observation; knows no recording length or labels."""
 def __init__(self):
  self.trace=[];self.off=None;self.restart=None;self.recent=deque(maxlen=10);self.active_n=0;self.event_id=0;self.last=0;self.seen_active=False
 def emit(self,stage,event,frame,**extra):
  self.trace.append(dict(stage=stage,event_id=event['event_id'],decision_frame=frame,outcome='UNKNOWN',off_start=event['off_start'],**extra))
 def end_window(self,frame,reason):
  e=self.restart;post=stats(e['post']);pre=e['pre']
  extra=dict(completed_off=e['completed_off'],pre=pre,post=post,preceding_active_duration=e['preceding_active_duration'],window_reason=reason,first_restart_frame=e['first_restart_frame'],latency_restart=frame-e['first_restart_frame'])
  for k in METRICS:extra['delta_'+k]=post[k+'_mean']-pre[k+'_mean'] if post[k+'_mean'] is not None and pre[k+'_mean'] is not None else None
  self.emit('T3',e,frame,**extra);self.restart=None
 def update(self,r):
  assert r['frame']==self.last+1,'Noncontiguous input requires an explicit quality policy'
  self.last=r['frame'];off=r['classification']=='LASER_OFF'
  if off:
   if self.restart:self.end_window(self.last,'next_OFF_short_window')
   if self.off is None:
    self.event_id+=1;self.off=dict(event_id=self.event_id,off_start=self.last,pre=stats(list(self.recent)),preceding_active_duration=self.active_n,startup=not self.seen_active)
    self.emit('T0',self.off,self.last,pre=self.off['pre'],preceding_active_duration=self.active_n,startup=self.off['startup'])
    self.recent.clear();self.active_n=0
   self.emit('T1',self.off,self.last,elapsed_off=self.last-self.off['off_start']+1)
  else:
   if self.off:
    e=self.off;self.off=None;e.update(completed_off=self.last-e['off_start'],first_restart_frame=self.last,post=[])
    self.emit('T2',e,self.last,completed_off=e['completed_off'],pre=e['pre'],preceding_active_duration=e['preceding_active_duration'],startup=e['startup'],first_restart={k:r[k] for k in METRICS})
    self.restart=e
   self.seen_active=True;self.active_n+=1;self.recent.append(r)
   if self.restart:
    self.restart['post'].append(r)
    if len(self.restart['post'])==10:self.end_window(self.last,'ten_active_frames')
 def close(self):
  # Explicit recording-close notification; excluded from ordinary-prefix comparisons.
  if self.restart:self.end_window(self.last,'stream_closed_short_window')
  if self.off:self.emit('CENSORED',self.off,self.last,elapsed_off=self.last-self.off['off_start']+1,startup=self.off['startup'])
