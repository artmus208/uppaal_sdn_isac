"""Native Windows API only. No verifier is invoked by identity/PE inspection.

Job membership is assigned atomically by CreateProcessW JOB_LIST (Windows 10+).
Only the watchdog owns the non-inheritable job handle: kill-on-close survives
watchdog termination, including between CreateProcess and ResumeThread.
"""
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys

SIZE=C.c_size_t
ULONG_PTR=SIZE
class IO_COUNTERS(C.Structure):
    _fields_=[(n,C.c_ulonglong) for n in ('ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]
class BASIC_LIMIT(C.Structure):
    _fields_=[('PerProcessUserTimeLimit',C.c_longlong),('PerJobUserTimeLimit',C.c_longlong),('LimitFlags',W.DWORD),('MinimumWorkingSetSize',SIZE),('MaximumWorkingSetSize',SIZE),('ActiveProcessLimit',W.DWORD),('Affinity',ULONG_PTR),('PriorityClass',W.DWORD),('SchedulingClass',W.DWORD)]
class EXT_LIMIT(C.Structure):
    _fields_=[('BasicLimitInformation',BASIC_LIMIT),('IoInfo',IO_COUNTERS),('ProcessMemoryLimit',SIZE),('JobMemoryLimit',SIZE),('PeakProcessMemoryUsed',SIZE),('PeakJobMemoryUsed',SIZE)]
class ACCOUNTING(C.Structure):
    _fields_=[(n,C.c_longlong) for n in ('TotalUserTime','TotalKernelTime','ThisPeriodTotalUserTime','ThisPeriodTotalKernelTime')]+[(n,W.DWORD) for n in ('TotalPageFaultCount','TotalProcesses','ActiveProcesses','TotalTerminatedProcesses')]
class MEMORY(C.Structure):
    _fields_=[('cb',W.DWORD),('PageFaultCount',W.DWORD)]+[(n,SIZE) for n in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
class RAM(C.Structure):
    _fields_=[('dwLength',W.DWORD),('dwMemoryLoad',W.DWORD)]+[(n,C.c_ulonglong) for n in ('ullTotalPhys','ullAvailPhys','ullTotalPageFile','ullAvailPageFile','ullTotalVirtual','ullAvailVirtual','ullAvailExtendedVirtual')]
class STARTUP(C.Structure):
    _fields_=[('cb',W.DWORD),('lpReserved',W.LPWSTR),('lpDesktop',W.LPWSTR),('lpTitle',W.LPWSTR)]+[(n,W.DWORD) for n in ('dwX','dwY','dwXSize','dwYSize','dwXCountChars','dwYCountChars','dwFillAttribute','dwFlags')]+[('wShowWindow',W.WORD),('cbReserved2',W.WORD),('lpReserved2',C.c_void_p),('hStdInput',W.HANDLE),('hStdOutput',W.HANDLE),('hStdError',W.HANDLE)]
class STARTUP_EX(C.Structure):
    _fields_=[('StartupInfo',STARTUP),('lpAttributeList',C.c_void_p)]
class PROCESS_INFO(C.Structure):
    _fields_=[('hProcess',W.HANDLE),('hThread',W.HANDLE),('dwProcessId',W.DWORD),('dwThreadId',W.DWORD)]
class PROCESS_ENTRY(C.Structure):
    _fields_=[('dwSize',W.DWORD),('cntUsage',W.DWORD),('th32ProcessID',W.DWORD),('th32DefaultHeapID',ULONG_PTR),('th32ModuleID',W.DWORD),('cntThreads',W.DWORD),('th32ParentProcessID',W.DWORD),('pcPriClassBase',W.LONG),('dwFlags',W.DWORD),('szExeFile',W.WCHAR*260)]

def native():
    if os.name!='nt' or platform.system()!='Windows':
        raise RuntimeError('Native Windows Python is required; WSL/Linux Python is rejected')

if os.name=='nt':
    K=C.WinDLL('kernel32',use_last_error=True)
    P=C.WinDLL('psapi',use_last_error=True)
    def bind(lib,name,args,result=W.BOOL):
        f=getattr(lib,name);f.argtypes=args;f.restype=result;return f
    close=bind(K,'CloseHandle',[W.HANDLE])
    create_job=bind(K,'CreateJobObjectW',[C.c_void_p,W.LPCWSTR],W.HANDLE)
    set_job=bind(K,'SetInformationJobObject',[W.HANDLE,C.c_int,C.c_void_p,W.DWORD])
    query_job=bind(K,'QueryInformationJobObject',[W.HANDLE,C.c_int,C.c_void_p,W.DWORD,C.c_void_p])
    terminate_job=bind(K,'TerminateJobObject',[W.HANDLE,W.UINT])
    initialize=bind(K,'InitializeProcThreadAttributeList',[C.c_void_p,W.DWORD,W.DWORD,C.POINTER(SIZE)])
    update=bind(K,'UpdateProcThreadAttribute',[C.c_void_p,W.DWORD,SIZE,C.c_void_p,SIZE,C.c_void_p,C.c_void_p])
    delete=bind(K,'DeleteProcThreadAttributeList',[C.c_void_p],None)
    create=bind(K,'CreateProcessW',[W.LPCWSTR,W.LPWSTR,C.c_void_p,C.c_void_p,W.BOOL,W.DWORD,C.c_void_p,W.LPCWSTR,C.c_void_p,C.POINTER(PROCESS_INFO)])
    resume=bind(K,'ResumeThread',[W.HANDLE],W.DWORD)
    wait=bind(K,'WaitForSingleObject',[W.HANDLE,W.DWORD],W.DWORD)
    exit_code=bind(K,'GetExitCodeProcess',[W.HANDLE,C.POINTER(W.DWORD)])
    open_process=bind(K,'OpenProcess',[W.DWORD,W.BOOL,W.DWORD],W.HANDLE)
    in_job=bind(K,'IsProcessInJob',[W.HANDLE,W.HANDLE,C.POINTER(W.BOOL)])
    memory_info=bind(P,'GetProcessMemoryInfo',[W.HANDLE,C.POINTER(MEMORY),W.DWORD])
    ram_info=bind(K,'GlobalMemoryStatusEx',[C.POINTER(RAM)])
    snapshot=bind(K,'CreateToolhelp32Snapshot',[W.DWORD,W.DWORD],W.HANDLE)
    first=bind(K,'Process32FirstW',[W.HANDLE,C.POINTER(PROCESS_ENTRY)])
    next_process=bind(K,'Process32NextW',[W.HANDLE,C.POINTER(PROCESS_ENTRY)])
    move=bind(K,'MoveFileExW',[W.LPCWSTR,W.LPCWSTR,W.DWORD])

def checked(value):
    if not value:raise C.WinError(C.get_last_error())
    return value

def completed(handle):
    result=wait(handle,0)
    if result==0xFFFFFFFF:raise C.WinError(C.get_last_error())
    return result==0

def pe_info(path):
    data=Path(path).read_bytes()
    if len(data)<64 or data[:2]!=b'MZ':raise ValueError('Expected Windows PE executable (MZ)')
    offset=struct.unpack_from('<I',data,60)[0]
    if offset+26>len(data) or data[offset:offset+4]!=b'PE\0\0':raise ValueError('Invalid PE signature/header')
    machine=struct.unpack_from('<H',data,offset+4)[0]
    flags=struct.unpack_from('<H',data,offset+22)[0]
    magic=struct.unpack_from('<H',data,offset+24)[0]
    if not flags&2 or flags&0x2000 or (machine,magic) not in [(0x14c,0x10b),(0x8664,0x20b)]:
        raise ValueError('Expected executable x86/x64 PE, not DLL or incompatible architecture')
    return dict(sha256=hashlib.sha256(data).hexdigest(),machine=hex(machine),optional_header=hex(magic),bytes=len(data))

def identity():
    native()
    import winreg
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\Microsoft\Cryptography',0,winreg.KEY_READ|winreg.KEY_WOW64_64KEY) as key:
        machine=winreg.QueryValueEx(key,'MachineGuid')[0]
    ram=RAM();ram.dwLength=C.sizeof(ram);checked(ram_info(C.byref(ram)))
    python=str(Path(sys.executable).resolve())
    return dict(os='Windows',native_host=platform.node(),machine_guid_sha256=hashlib.sha256(machine.encode()).hexdigest(),
                python_path=python,python_sha256=pe_info(python)['sha256'],python_version=sys.version,
                platform=platform.platform(),physical_ram_bytes=ram.ullTotalPhys,logical_cpu_count=os.cpu_count(),processor=platform.processor())

def existing_verifiers():
    native();h=snapshot(2,0)
    if h==C.c_void_p(-1).value:raise C.WinError(C.get_last_error())
    result=[]
    try:
        e=PROCESS_ENTRY();e.dwSize=C.sizeof(e)
        ok=first(h,C.byref(e))
        while ok:
            if e.szExeFile.casefold().startswith('verifyta'):result.append(dict(pid=e.th32ProcessID,name=e.szExeFile))
            ok=next_process(h,C.byref(e))
        if C.get_last_error()!=18:raise C.WinError(C.get_last_error())
    finally:close(h)
    return result

class Job:
    def __init__(self):
        native();self.handle=checked(create_job(None,None));self.process=None;self.thread=None
        try:
            limits=EXT_LIMIT();limits.BasicLimitInformation.LimitFlags=0x2000 # KILL_ON_JOB_CLOSE, no breakaway
            checked(set_job(self.handle,9,C.byref(limits),C.sizeof(limits)))
        except BaseException:self.close();raise

    def launch(self,command,cwd,stdout,stderr):
        import msvcrt
        size=SIZE();initialize(None,2,0,C.byref(size))
        attrs=C.create_string_buffer(size.value);checked(initialize(attrs,2,0,C.byref(size)))
        handles=[]
        try:
            with open(os.devnull,'rb') as inp,open(stdout,'xb',buffering=0) as out,open(stderr,'xb',buffering=0) as err:
                handles=[msvcrt.get_osfhandle(f.fileno()) for f in (inp,out,err)]
                for h in handles:os.set_handle_inheritable(h,True)
                inherited=(W.HANDLE*3)(*handles);jobs=(W.HANDLE*1)(self.handle)
                checked(update(attrs,0,0x20002,inherited,C.sizeof(inherited),None,None)) # HANDLE_LIST
                checked(update(attrs,0,0x2000D,jobs,C.sizeof(jobs),None,None)) # JOB_LIST
                si=STARTUP_EX();si.StartupInfo.cb=C.sizeof(si);si.lpAttributeList=C.cast(attrs,C.c_void_p)
                si.StartupInfo.dwFlags=0x100
                si.StartupInfo.hStdInput,si.StartupInfo.hStdOutput,si.StartupInfo.hStdError=handles
                pi=PROCESS_INFO();cmd=C.create_unicode_buffer(subprocess.list2cmdline(command))
                checked(create(command[0],cmd,None,None,True,0x80000|0x4|0x08000000,None,cwd,C.byref(si),C.byref(pi)))
                self.process=pi.hProcess;self.thread=pi.hThread;self.pid=pi.dwProcessId
        finally:delete(attrs)

    def start(self):
        if resume(self.thread)==0xFFFFFFFF:raise C.WinError(C.get_last_error())
        close(self.thread);self.thread=None

    def accounting(self):
        a=ACCOUNTING();checked(query_job(self.handle,1,C.byref(a),C.sizeof(a),None));return a

    def pids(self):
        capacity=64
        while capacity<=1048576:
            data=C.create_string_buffer(8+capacity*C.sizeof(ULONG_PTR))
            if query_job(self.handle,3,data,len(data),None):
                count=C.cast(data,C.POINTER(W.DWORD))[1]
                return list((ULONG_PTR*count).from_buffer(data,8))
            if C.get_last_error()!=234:raise C.WinError(C.get_last_error())
            capacity*=2
        raise RuntimeError('Job process list exceeds monitoring capacity')

    def has_live_descendants(self):
        # Job accounting can briefly still include the signaled/exited leader.
        # Inspect retained handles for other members, not the asynchronous count.
        for pid in self.pids():
            if pid==self.pid:continue
            h=open_process(0x100000|0x410,False,pid)
            if not h:
                if C.get_last_error()==87:continue
                raise C.WinError(C.get_last_error())
            try:
                owned=W.BOOL();checked(in_job(h,self.handle,C.byref(owned)))
                if owned.value and not completed(h):return True
            finally:close(h)
        return False

    def metrics(self):
        rss=0;peak_leader=0
        for pid in self.pids():
            h=open_process(0x100000|0x410,False,pid)
            if not h:
                if C.get_last_error()==87:continue # exited between enumeration and open
                raise C.WinError(C.get_last_error())
            try:
                owned=W.BOOL();checked(in_job(h,self.handle,C.byref(owned)))
                if not owned.value or completed(h):continue # exited / PID reused outside job
                m=MEMORY();m.cb=C.sizeof(m)
                if not memory_info(h,C.byref(m),m.cb):
                    if completed(h):continue
                    raise C.WinError(C.get_last_error())
                rss+=m.WorkingSetSize
                if pid==self.pid:peak_leader=m.PeakWorkingSetSize
            finally:close(h)
        # The retained leader handle preserves its peak even for a very fast command.
        m=MEMORY();m.cb=C.sizeof(m)
        if memory_info(self.process,C.byref(m),m.cb):peak_leader=max(peak_leader,m.PeakWorkingSetSize)
        a=self.accounting();limits=EXT_LIMIT();checked(query_job(self.handle,9,C.byref(limits),C.sizeof(limits),None))
        return dict(rss_bytes=rss,leader_peak_rss_bytes=peak_leader,cpu_seconds=(a.TotalUserTime+a.TotalKernelTime)/1e7,
                    live_processes=a.ActiveProcesses,peak_job_private_commit_bytes=limits.PeakJobMemoryUsed)

    def result_code(self):
        code=W.DWORD();checked(exit_code(self.process,C.byref(code)));return code.value

    def terminate(self):checked(terminate_job(self.handle,125))

    def close(self):
        # Closing the sole job handle is itself the crash-safe termination path.
        for name in ('handle','thread','process'):
            h=getattr(self,name,None)
            if h:close(h);setattr(self,name,None)

if __name__=='__main__':
    print(json.dumps(identity(),indent=2))
