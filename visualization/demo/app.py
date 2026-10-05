"""Local, single-session demonstration server. Run: python -B visualization/demo/app.py"""
import argparse
import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from replay_source import ReplaySource
from folder_source import FolderSimulationSource,metadata

class Handler(BaseHTTPRequestHandler):
    def send(self, value, status=200, mime='application/json'):
        body=value if isinstance(value,bytes) else json.dumps(value).encode()
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.end_headers();
        try:self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError):pass
    def do_GET(self):
        if self.path=='/':self.send(Path(__file__).with_name('index.html').read_bytes(),mime='text/html; charset=utf-8')
        elif self.path=='/state':self.send(self.server.source.snapshot())
        else:self.send({'error':'Not found'},404)
    def do_POST(self):
        try:
            data=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))) or b'{}')
            if not isinstance(data,dict): raise ValueError('Expected object')
            state=self.server.source.snapshot()
            if data.get('session')!=state['session'] or data.get('revision')!=state['revision']:
                self.send({'error':'Stale session; state refreshed. Retry control.', 'state':state},409);return
            if self.path=='/choose':
                kind=data.get('kind')
                if kind not in ('file','folder'):raise ValueError('Invalid chooser')
                chosen=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('choose_path.py')),kind],capture_output=True,text=True,timeout=120)
                if chosen.returncode:raise ValueError('Native chooser unavailable; enter an absolute local path')
                self.send({'path':chosen.stdout.strip()});return
            if self.path=='/start':
                if data.get('mode')=='Folder Simulation':
                    source=FolderSimulationSource(data.get('folder',''),data.get('gcode',''),data.get('first_index'))
                elif data.get('mode')=='Artifact Replay':
                    source=ReplaySource();source.selected_gcode=metadata(data['gcode']) if data.get('gcode') else None
                else:raise ValueError('Invalid mode')
                self.server.source=source;self.send(source.snapshot());return
            if self.path=='/stop':
                if not hasattr(self.server.source,'stop'):raise ValueError('Stop is folder-only')
                self.send(self.server.source.stop());return
            if self.path=='/advance':self.send(self.server.source.advance(data.get('count',1)))
            elif self.path=='/jump':self.send(self.server.source.jump(data.get('frame')))
            elif self.path=='/reset':self.send(self.server.source.reset())
            else:self.send({'error':'Not found'},404)
        except (ValueError,TypeError,OSError,subprocess.TimeoutExpired) as e:self.send({'error':str(e)},400)
    def log_message(self,*args):pass

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);args=p.parse_args()
    try:server=HTTPServer(('127.0.0.1',args.port),Handler)
    except OSError as e:sys.exit(f'Cannot bind local demo port {args.port}: {e}. Close the prior demo or choose --port <unused port>.')
    server.source=ReplaySource()
    print(f'MPAP demo: http://127.0.0.1:{args.port} — single shared replay session',flush=True)
    server.timeout=.1
    try:
        while True:
            if hasattr(server.source,'poll'):server.source.poll()
            server.handle_request()
    except KeyboardInterrupt:pass
    finally:server.server_close()
