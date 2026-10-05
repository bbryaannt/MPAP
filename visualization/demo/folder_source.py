"""Conservative loopback-demo ingestion. G-code is metadata, never engine input."""
import re,struct,time,uuid,sys,math
from pathlib import Path
from collections import deque
from replay_source import ReplaySource,ROOT
from causal_events import Replay
from thermal_preview import preview
sys.path.insert(0,str(ROOT))
from pipeline.pipeline import MeltPoolPipeline

class Pending(Exception):pass

def metadata(path):
    p=Path(path).expanduser().resolve(strict=True)
    if not p.is_file():raise ValueError('G-code must be a file')
    if p.suffix.lower() not in ('.mpf','.nc','.gcode','.tap','.txt'):raise ValueError('Unsupported G-code extension')
    with p.open('rb') as f:f.read(1)
    return {'path':str(p),'bytes':p.stat().st_size,'usage':'Configuration only; not parsed for inference'}

def ready_payload(path):
    size=path.stat().st_size
    with path.open('rb') as f:raw=f.read(36)
    if len(raw)<2:raise Pending('Incomplete schema marker')
    if raw[:2]==b'\0\0':
        if len(raw)<36:raise Pending('Incomplete schema-1 prefix')
        schema,words,left,top,right,bottom,width,bits,fmt=struct.unpack('<9I',raw)
        header=words*4;height=bottom-top
        if schema!=0 or header<36 or header>65536:raise ValueError('Invalid/unsupported schema-1 header length (demo max64KiB)')
    else:
        if len(raw)<8:raise Pending('Incomplete schema-0 prefix')
        height,width,bits,fmt=struct.unpack('<HHHH',raw[:8]);header=8
    if width<=0 or height<=0 or width*height>16000000:raise ValueError('Invalid dimensions / demo limit16M pixels')
    if bits not in (8,12):raise ValueError('Unsupported bit depth')
    if fmt not in (0,1):raise ValueError('Unrecognized pixel format; prototype accepts observed codes0/1')
    expected=header+(width*height if bits==8 else ((width*height+1)//2)*3)
    if size<expected:raise Pending(f'Incomplete payload: {size}/{expected} bytes')
    if size>expected:raise ValueError(f'Unexpected trailing bytes: {size}/{expected}; blocked for inspection')
    return expected

class FolderSimulationSource(ReplaySource):
    def __init__(self,directory,gcode,first_index=None,pipeline=None,clock=time.monotonic,visualization=True):
        if not directory or not gcode:raise ValueError('Select both a thermal folder and G-code file')
        self.directory=Path(directory).expanduser().resolve(strict=True)
        if not self.directory.is_dir():raise ValueError('Thermal path must be a directory')
        self.gcode=metadata(gcode)
        self.visualization=visualization;self.thermal=None;self.encoding_seconds=0.
        if first_index is not None and (type(first_index) is not int or first_index<0):raise ValueError('First index must be nonnegative')
        self.pipeline=pipeline or MeltPoolPipeline();self.clock=clock
        self.session=str(uuid.uuid4());self.revision=0;self.history_limit=600;self.error=None;self.frames=[];self.events=[]
        ReplaySource.reset(self)
        self.engine=Replay();self.observed={};self.processed={};self.expected=first_index;self.first_index=first_index
        self.running=True;self.lifecycle='WAITING FOR DATA';self.detail='Existing files included in this new session; awaiting ready data'
        self.last_scan=-float('inf');self.processing_seconds=0.
    def advance(self,count=1):raise ValueError('Folder mode advances only through incoming files')
    def jump(self,frame):raise ValueError('Jump is replay-only')
    def reset(self):raise ValueError('Start a new session to reset folder monitoring')
    def stop(self):
        self.running=False;self.lifecycle='STOPPED';self.detail='Monitoring stopped';self.revision+=1
        return self.snapshot()
    def poll(self):
        now=self.clock()
        if not self.running or self.error or now-self.last_scan<.25:return
        self.last_scan=now
        try:
            if not Path(self.gcode["path"]).is_file():raise ValueError("Selected G-code disappeared; configuration unavailable")
            indexed={}
            for p in self.directory.iterdir():
                if p.suffix.lower()!='.dat':continue
                m=re.fullmatch(r'Image(\d+)\.dat',p.name,re.I)
                if not m or not p.is_file() or p.is_symlink():raise ValueError(f'Unsupported incoming file: {p.name}; expected Image<index>.dat regular files')
                i=int(m[1])
                if i in indexed:raise ValueError(f'Duplicate filename index {i}')
                indexed[i]=p
            for i,(name,sig) in self.processed.items():
                p=indexed.get(i)
                if p is None or p.name!=name or self.signature(p)!=sig:raise ValueError(f'Processed file changed/removed: index {i}')
            pending=[i for i in sorted(indexed) if i not in self.processed]
            if self.processed and pending and pending[0]<max(self.processed):raise ValueError(f'Late lower index {pending[0]}; history not reordered')
            if self.expected is None and pending:self.expected=pending[0]
            self.lifecycle='WAITING FOR DATA';self.detail='Waiting for files'
            for i in pending:
                sig=self.signature(indexed[i])
                if i not in self.observed or self.observed[i][0]!=sig:self.observed[i]=(sig,now)
            start=time.perf_counter()
            for i in pending:
                if time.perf_counter()-start>.08:break
                if i!=self.expected:
                    self.lifecycle='DATA QUALITY ISSUE';self.detail=f'Index gap: awaiting {self.expected}; found {i}. No history bridged';break
                p=indexed[i];sig=self.signature(p);prior=self.observed.get(i)
                if not prior or prior[0]!=sig:
                    self.observed[i]=(sig,now);self.detail=f'{p.name}: pending stable size/mtime';break
                if now-prior[1]<.25:break
                try:ready_payload(p)
                except Pending as e:self.detail=f'{p.name}: {e}; pending retry';break
                decoded=self.pipeline.decoder.decode(p)
                if self.signature(p)!=sig:self.observed[i]=(self.signature(p),now);break
                began=time.perf_counter();result=self.pipeline.process_decoded(decoded,frame_number=self.cursor+1,file_path=p);self.processing_seconds+=time.perf_counter()-began
                if self.signature(p)!=sig:raise ValueError(f'{p.name} changed during processing; no frame committed')
                row=dict(frame=self.cursor+1,filename=p.name,classification=result.classification.value,area_px=float(result.features.area_px),aspect_ratio=float(result.features.aspect_ratio),circularity=float(result.features.circularity),band3=float(result.band_counts.band3),band4=float(result.band_counts.band4),band5=float(result.band_counts.band5))
                if not all(math.isfinite(row[k]) for k in ('area_px','aspect_ratio','circularity','band3','band4','band5')):raise ValueError('Nonfinite pipeline result')
                self.engine.update(row);emitted=self.engine.trace;self.engine.trace=[]
                self.accept(row,emitted)
                if self.visualization:
                    began=time.perf_counter();self.thermal=preview(decoded);self.thermal["frame"]=self.cursor
                    self.encoding_seconds+=time.perf_counter()-began
                retained={e['event_id'] for e in self.recent}
                if self.evidence:retained.add(self.evidence['event_id'])
                self.inspections={k:v for k,v in self.inspections.items() if k in retained}
                self.processed[i]=(p.name,sig);self.expected=i+1;self.revision+=1
                self.lifecycle='PROCESSING';self.detail=f'Processed {p.name}'
        except Exception as e:
            self.error=f'{type(e).__name__}: {e}';self.lifecycle='DATA QUALITY ISSUE';self.detail='Processing blocked; correct inputs and start a new session';self.revision+=1
    @staticmethod
    def signature(p):
        st=p.stat();return (st.st_size,st.st_mtime_ns,st.st_ino)
    def snapshot(self):
        s=ReplaySource.snapshot(self)
        s.update(first_index=getattr(self,'first_index',None),thermal=getattr(self,'thermal',None),encoding_seconds=getattr(self,'encoding_seconds',0),mode='Folder Simulation',source=str(getattr(self,'directory','')),total_frames=None,finished=False,gcode=getattr(self,'gcode',None),lifecycle=getattr(self,'lifecycle','NOT STARTED'),detail=getattr(self,'detail',''),data_quality='ERROR' if self.error else 'PENDING' if getattr(self,'lifecycle','')=='DATA QUALITY ISSUE' else 'VALID',processing_seconds=getattr(self,'processing_seconds',0))
        return s
