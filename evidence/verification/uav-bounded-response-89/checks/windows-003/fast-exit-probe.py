import sys, tempfile, time, json, ctypes
from pathlib import Path
sys.path.insert(0, r'\\wsl.localhost\Ubuntu\tmp\uppaal-owner-89\evidence\verification\uav-bounded-response-89')
import windows_native as w
with tempfile.TemporaryDirectory() as d:
    for i in range(20):
        job=w.Job()
        try:
            job.launch([sys.executable,'-c','pass'],d,str(Path(d)/f'{i}.out'),str(Path(d)/f'{i}.err'));job.start()
            while not w.completed(job.process):time.sleep(.005)
            ids=job.pids();names=[]
            if job.has_live_descendants():
                snap=w.snapshot(2,0);e=w.PROCESS_ENTRY();e.dwSize=ctypes.sizeof(e)
                ok=w.first(snap,ctypes.byref(e))
                while ok:
                    if e.th32ProcessID in ids:names.append((e.th32ProcessID,e.szExeFile))
                    ok=w.next_process(snap,ctypes.byref(e))
                w.close(snap)
                start=time.monotonic()
                while job.has_live_descendants() and time.monotonic()-start<.5:time.sleep(.005)
                print(json.dumps(dict(attempt=i,leader=job.pid,remaining=names,natural_cleanup_seconds=time.monotonic()-start,still_live=job.has_live_descendants())),flush=True)
        finally:job.close()
