"""Read-only artifact adapter. No runtime or research module imports."""
import os
import csv
import json
import math
import uuid
import copy
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Optional private artifacts are explicitly supplied by the operator, never bundled.
FEATURES = Path(os.environ['MPAP_REPLAY_FEATURES']).expanduser() if os.environ.get('MPAP_REPLAY_FEATURES') else None
TRACE = Path(os.environ['MPAP_REPLAY_TRACE']).expanduser() if os.environ.get('MPAP_REPLAY_TRACE') else None

class ReplaySource:
    def __init__(self, features=FEATURES, trace=TRACE, history_limit=600):
        self.session = str(uuid.uuid4())
        self.revision = 0
        self.history_limit = history_limit
        self.error = None
        self.frames, self.events = [], []
        try:
            if features is None or trace is None:raise ValueError('Replay artifacts not configured. Choose Folder Simulation, or set MPAP_REPLAY_FEATURES and MPAP_REPLAY_TRACE before launch.')
            with features.open() as f:
                for i, row in enumerate(csv.DictReader(f), 1):
                    if int(row['frame']) != i:
                        raise ValueError(f'Frame {i}: duplicate, missing or unordered frame ID')
                    if not row['filename'] or row['classification'] not in {'LASER_OFF','LOW_POWER','LOW_POWDER','GOOD','HIGH_POWER','UNKNOWN'}:
                        raise ValueError(f'Frame {i}: invalid identity/classification')
                    row['frame'] = i
                    for k in ('area_px','aspect_ratio','circularity','band3','band4','band5'):
                        row[k] = float(row[k])
                        if not math.isfinite(row[k]) or row[k] < 0:
                            raise ValueError(f'Frame {i}: invalid {k}')
                    self.frames.append(row)
            if not self.frames: raise ValueError('Empty frame source')
            if len({r['filename'] for r in self.frames}) != len(self.frames):
                raise ValueError('Duplicate source filename')
            with trace.open() as f:
                self.events = [json.loads(line) for line in f]
            # Independently check the availability schedule, without interpreting transitions.
            expected=[]; event=0;off_start=None;restart=None
            for r in self.frames:
                i=r['frame']
                if r['classification']=='LASER_OFF':
                    if restart is not None:
                        expected.append(('T3',event,i));restart=None
                    if off_start is None:
                        event+=1;off_start=i;expected.append(('T0',event,i))
                    expected.append(('T1',event,i))
                else:
                    if off_start is not None:
                        expected.append(('T2',event,i));off_start=None;restart=i
                    if restart is not None and i-restart==9:
                        expected.append(('T3',event,i));restart=None
            if restart is not None:expected.append(('T3',event,len(self.frames)))
            if off_start is not None:expected.append(('CENSORED',event,len(self.frames)))
            if [(e['stage'],e['event_id'],e['decision_frame']) for e in self.events] != expected:
                raise ValueError('Trace availability schedule disagrees with frame classifications')
            def finite(x):
                if isinstance(x,dict):return all(finite(v) for v in x.values())
                if isinstance(x,list):return all(finite(v) for v in x)
                return not isinstance(x,float) or math.isfinite(x)
            for e in self.events:
                if e['outcome']!='UNKNOWN' or not finite(e):raise ValueError('Invalid trace outcome/numeric value')
                required={'T0':('pre','preceding_active_duration'),'T1':('elapsed_off',),'T2':('completed_off','first_restart'),'T3':('completed_off','post','delta_area_px','delta_aspect_ratio'),'CENSORED':('elapsed_off',)}[e['stage']]
                if any(k not in e for k in required):raise ValueError('Missing trace evidence field')
                for key in ('elapsed_off','completed_off','preceding_active_duration','off_start'):
                    if key in e and (type(e[key]) is not int or e[key]<0):raise ValueError('Invalid trace count')
                for side in ('pre','post'):
                    if side not in e:continue
                    window=e[side]
                    if type(window.get('n')) is not int or not 0<=window['n']<=10:raise ValueError('Invalid window sample count')
                    for metric in ('area_px','aspect_ratio','circularity','band3'):
                        for stat in ('mean','std','slope'):
                            value=window[metric+'_'+stat]
                            if value is not None and (type(value) not in (int,float) or not math.isfinite(value)):raise ValueError('Invalid window metric')
                            if value is None and window['n'] >= (2 if stat=='slope' else 1):raise ValueError('Missing window metric')
                for key in ('delta_area_px','delta_aspect_ratio'):
                    if key in e and e[key] is not None and type(e[key]) not in (int,float):raise ValueError('Invalid delta')

        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            self.error = f'{type(error).__name__}: {error}'
            self.frames, self.events = [], []
        self.reset()

    def reset(self):
        self.revision += 1
        self.history = deque(maxlen=self.history_limit)
        self.cursor = self.event_cursor = 0
        self.latest = None
        self.recent = []
        self.inspections = {}
        self.stage = 'AWAITING REPLAY'
        self.evidence = None
        return self.snapshot()

    def advance(self, count=1):
        if self.error: raise ValueError(self.error)
        if type(count) is not int or not 1 <= count <= 1000: raise ValueError('count must be an integer from 1 to 1000')
        self.revision += 1
        for _ in range(count):
            if self.cursor == len(self.frames): break
            available=[]
            while self.event_cursor<len(self.events) and self.events[self.event_cursor]['decision_frame']<=self.cursor+1:
                available.append(self.events[self.event_cursor]);self.event_cursor+=1
            self.accept(self.frames[self.cursor],available)
        retained={e['event_id'] for e in self.recent}
        if self.evidence:retained.add(self.evidence['event_id'])
        self.inspections={k:v for k,v in self.inspections.items() if k in retained}
        return self.snapshot()

    def accept(self, row, events):
        self.latest = row
        self.cursor += 1
        self.history.append({k:self.latest[k] for k in ('frame','classification','area_px','aspect_ratio','band3')})
        emitted = False
        for event in events:
            assert event['decision_frame'] == self.cursor
            self.stage = event['stage']
            self.evidence = event
            eid=event['event_id']
            if eid not in self.inspections:
                self.inspections[eid] = {'event_id':eid,'off_start':event['off_start'],'stages':{},'status':'UNKNOWN / RESEARCH'}
            item=self.inspections[eid]
            item['stages'][event['stage']]=event['decision_frame']
            for key in ('startup','pre','elapsed_off','completed_off','post','delta_area_px','delta_aspect_ratio','delta_band3','window_reason'):
                if key in event:item[key]=event[key]
            if event['stage']=='T2':item['off_end']=event['decision_frame']-1
            if event['stage']=='CENSORED':item['censored']=True
            # Keep only events referenced by the bounded log, plus the current event.

            emitted = True
            if event['stage'] != 'T1':
                self.recent = (self.recent + [event])[-8:]
        if not emitted and self.latest['classification'] != 'LASER_OFF':
            self.stage = 'RESTART WINDOW' if self.evidence and self.evidence['stage']=='T2' else 'ACTIVE'

    def jump(self, frame):
        if self.error:raise ValueError(self.error)
        if type(frame) is not int or not 0<=frame<=len(self.frames):raise ValueError('Target frame outside recording')
        self.reset()
        while self.cursor<frame:self.advance(min(1000,frame-self.cursor))
        return self.snapshot()

    def snapshot(self):
        inspections=copy.deepcopy(list(self.inspections.values()))
        for item in inspections:
            if 'post' in item:item['restart_n']=item['post']['n']
            elif 'T2' in item['stages']:item['restart_n']=min(10,self.cursor-item['stages']['T2']+1)
            else:item['restart_n']=0
            item['context']=('Startup OFF; no preceding active window. ' if item.get('startup') else '') + ('Recording ended while OFF; right-censored, not confirmed physical shutdown.' if item.get('censored') else 'OFF ongoing; end/duration not completed.' if 'T2' not in item['stages'] else 'Restart window incomplete; deltas unavailable.' if 'T3' not in item['stages'] else 'Short restart window; actual sample count retained.' if item.get('post',{}).get('n',10)<10 else 'Restart evidence available.')
        return dict(mode='Artifact Replay',lifecycle='REPLAY',gcode=getattr(self,'selected_gcode',None),inspections=inspections,session=self.session,revision=self.revision,data_quality='ERROR' if self.error else 'VALID',error=self.error,history=list(self.history),history_limit=self.history_limit,frame=self.cursor,total_frames=len(self.frames),finished=bool(self.frames) and self.cursor==len(self.frames),
                    current=self.latest,stage=self.stage,evidence=self.evidence,events=self.recent,
                    source='Stored feature CSV + causal trace',inference='RESEARCH / UNRESOLVED')
