import sys, tempfile, time, json, ctypes
from pathlib import Path
sys.path.insert(0, r'\\wsl.localhost\Ubuntu\tmp\uppaal-owner-89\evidence\verification\uav-bounded-response-89')
import windows_native as w
image=w.bind(w.K,'QueryFullProcessImageNameW',[w.W.HANDLE,w.W.DWORD,w.W.LPWSTR,ctypes.POINTER(w.W.DWORD)])
with tempfile.TemporaryDirectory() as d:
    for i in range(40):
        job=w.Job()
        try:
            job.launch([sys.executable,'-c','pass'],d,str(Path(d)/f'{i}.out'),str(Path(d)/f'{i}.err'));job.start()
            while not w.completed(job.process):time.sleep(.001)
            for pid in job.pids():
                if pid==job.pid:continue
                h=w.open_process(0x100000|0x410,False,pid)
                if not h:continue
                try:
                    before=w.completed(h);buf=ctypes.create_unicode_buffer(32768);size=w.W.DWORD(len(buf));ok=image(h,0,buf,ctypes.byref(size))
                    print(json.dumps(dict(attempt=i,leader=job.pid,other_pid=pid,already_exited=before,path=buf.value if ok else None)),flush=True)
                finally:w.close(h)
            start=time.monotonic()
            while job.has_live_descendants() and time.monotonic()-start<.5:time.sleep(.005)
        finally:job.close()
