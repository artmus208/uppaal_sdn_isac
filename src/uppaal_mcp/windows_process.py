"""Windows 10+ owned process tree; no external packages or shell commands.

The process joins a non-inheritable Job Object atomically at creation, before
its suspended thread resumes. Descendants cannot break away. Only standard
streams are inherited. Closing the job kills its remaining members.
"""
import ctypes as C
from ctypes import wintypes as W
import os
import subprocess
import time


SIZE = C.c_size_t


class IoCounters(C.Structure):
    _fields_ = [(n, C.c_ulonglong) for n in (
        'ReadOperationCount', 'WriteOperationCount', 'OtherOperationCount',
        'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]


class BasicLimit(C.Structure):
    _fields_ = [('PerProcessUserTimeLimit', C.c_longlong),
                ('PerJobUserTimeLimit', C.c_longlong), ('LimitFlags', W.DWORD),
                ('MinimumWorkingSetSize', SIZE), ('MaximumWorkingSetSize', SIZE),
                ('ActiveProcessLimit', W.DWORD), ('Affinity', SIZE),
                ('PriorityClass', W.DWORD), ('SchedulingClass', W.DWORD)]


class ExtendedLimit(C.Structure):
    _fields_ = [('BasicLimitInformation', BasicLimit), ('IoInfo', IoCounters)] + [
        (n, SIZE) for n in ('ProcessMemoryLimit', 'JobMemoryLimit',
                           'PeakProcessMemoryUsed', 'PeakJobMemoryUsed')]


class Accounting(C.Structure):
    _fields_ = [(n, C.c_longlong) for n in (
        'TotalUserTime', 'TotalKernelTime', 'ThisPeriodTotalUserTime',
        'ThisPeriodTotalKernelTime')] + [(n, W.DWORD) for n in (
        'TotalPageFaultCount', 'TotalProcesses', 'ActiveProcesses',
        'TotalTerminatedProcesses')]


class Memory(C.Structure):
    _fields_ = [('cb', W.DWORD), ('PageFaultCount', W.DWORD)] + [(n, SIZE) for n in (
        'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
        'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
        'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]


class Startup(C.Structure):
    _fields_ = [('cb', W.DWORD), ('lpReserved', W.LPWSTR),
                ('lpDesktop', W.LPWSTR), ('lpTitle', W.LPWSTR)] + [
        (n, W.DWORD) for n in ('dwX', 'dwY', 'dwXSize', 'dwYSize',
                              'dwXCountChars', 'dwYCountChars',
                              'dwFillAttribute', 'dwFlags')] + [
        ('wShowWindow', W.WORD), ('cbReserved2', W.WORD),
        ('lpReserved2', C.c_void_p), ('hStdInput', W.HANDLE),
        ('hStdOutput', W.HANDLE), ('hStdError', W.HANDLE)]


class StartupEx(C.Structure):
    _fields_ = [('StartupInfo', Startup), ('lpAttributeList', C.c_void_p)]


class ProcessInfo(C.Structure):
    _fields_ = [('hProcess', W.HANDLE), ('hThread', W.HANDLE),
                ('dwProcessId', W.DWORD), ('dwThreadId', W.DWORD)]


if os.name == 'nt':
    kernel = C.WinDLL('kernel32', use_last_error=True)
    psapi = C.WinDLL('psapi', use_last_error=True)

    def bind(lib, name, args, result=W.BOOL):
        function = getattr(lib, name)
        function.argtypes, function.restype = args, result
        return function

    close_handle = bind(kernel, 'CloseHandle', [W.HANDLE])
    create_job = bind(kernel, 'CreateJobObjectW', [C.c_void_p, W.LPCWSTR], W.HANDLE)
    set_job = bind(kernel, 'SetInformationJobObject', [W.HANDLE, C.c_int, C.c_void_p, W.DWORD])
    query_job = bind(kernel, 'QueryInformationJobObject', [W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.c_void_p])
    terminate_job = bind(kernel, 'TerminateJobObject', [W.HANDLE, W.UINT])
    initialize_attributes = bind(kernel, 'InitializeProcThreadAttributeList', [C.c_void_p, W.DWORD, W.DWORD, C.POINTER(SIZE)])
    update_attribute = bind(kernel, 'UpdateProcThreadAttribute', [C.c_void_p, W.DWORD, SIZE, C.c_void_p, SIZE, C.c_void_p, C.c_void_p])
    delete_attributes = bind(kernel, 'DeleteProcThreadAttributeList', [C.c_void_p], None)
    create_process = bind(kernel, 'CreateProcessW', [W.LPCWSTR, W.LPWSTR, C.c_void_p, C.c_void_p, W.BOOL, W.DWORD, C.c_void_p, W.LPCWSTR, C.c_void_p, C.POINTER(ProcessInfo)])
    resume_thread = bind(kernel, 'ResumeThread', [W.HANDLE], W.DWORD)
    wait_handle = bind(kernel, 'WaitForSingleObject', [W.HANDLE, W.DWORD], W.DWORD)
    get_exit_code = bind(kernel, 'GetExitCodeProcess', [W.HANDLE, C.POINTER(W.DWORD)])
    open_process = bind(kernel, 'OpenProcess', [W.DWORD, W.BOOL, W.DWORD], W.HANDLE)
    is_in_job = bind(kernel, 'IsProcessInJob', [W.HANDLE, W.HANDLE, C.POINTER(W.BOOL)])
    memory_info = bind(psapi, 'GetProcessMemoryInfo', [W.HANDLE, C.POINTER(Memory), W.DWORD])


def checked(value):
    if not value:
        raise C.WinError(C.get_last_error())
    return value


def signaled(handle):
    result = wait_handle(handle, 0)
    if result == 0xFFFFFFFF:
        raise C.WinError(C.get_last_error())
    return result == 0


class WindowsProcess:
    """Small Popen-compatible owner for queue attempts, including descendants."""
    def __init__(self, command, cwd, stdout, stderr):
        if os.name != 'nt':
            raise RuntimeError('WindowsProcess requires native Windows Python')
        self.job = self.process = self.thread = None
        self.pid = None
        self.returncode = None
        self.peak = 0
        try:
            self.job = checked(create_job(None, None))
            limits = ExtendedLimit()
            limits.BasicLimitInformation.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE
            checked(set_job(self.job, 9, C.byref(limits), C.sizeof(limits)))
            self._launch(command, cwd, stdout, stderr)
            if resume_thread(self.thread) == 0xFFFFFFFF:
                raise C.WinError(C.get_last_error())
            close_handle(self.thread)
            self.thread = None
        except BaseException:
            self.close()
            raise

    def _launch(self, command, cwd, stdout, stderr):
        import msvcrt
        size = SIZE()
        initialize_attributes(None, 2, 0, C.byref(size))
        attrs = C.create_string_buffer(size.value)
        checked(initialize_attributes(attrs, 2, 0, C.byref(size)))
        handles = []
        previous = []
        try:
            with open(os.devnull, 'rb') as stdin:
                handles = [msvcrt.get_osfhandle(f.fileno()) for f in (stdin, stdout, stderr)]
                previous = [os.get_handle_inheritable(h) for h in handles]
                for h in handles:
                    os.set_handle_inheritable(h, True)
                inherited = (W.HANDLE * 3)(*handles)
                jobs = (W.HANDLE * 1)(self.job)
                checked(update_attribute(attrs, 0, 0x20002, inherited, C.sizeof(inherited), None, None))
                checked(update_attribute(attrs, 0, 0x2000D, jobs, C.sizeof(jobs), None, None))
                si = StartupEx()
                si.StartupInfo.cb = C.sizeof(si)
                si.lpAttributeList = C.cast(attrs, C.c_void_p)
                si.StartupInfo.dwFlags = 0x100  # USESTDHANDLES
                si.StartupInfo.hStdInput, si.StartupInfo.hStdOutput, si.StartupInfo.hStdError = handles
                pi = ProcessInfo()
                cmd = C.create_unicode_buffer(subprocess.list2cmdline(command))
                # JOB_LIST closes the unowned suspended-process race (Windows 10+).
                checked(create_process(command[0], cmd, None, None, True,
                                       0x80000 | 0x4 | 0x08000000, None, cwd,
                                       C.byref(si), C.byref(pi)))
                self.process, self.thread, self.pid = pi.hProcess, pi.hThread, pi.dwProcessId
                for h, old in zip(handles, previous):
                    os.set_handle_inheritable(h, old)
                handles = []
        finally:
            # Files are still open on the normal path; on error only the parent's
            # stdout/stderr need restoration after devnull has been closed.
            for h, old in zip(handles[1:], previous[1:]):
                os.set_handle_inheritable(h, old)
            delete_attributes(attrs)

    def accounting(self):
        info = Accounting()
        checked(query_job(self.job, 1, C.byref(info), C.sizeof(info), None))
        return info

    def pids(self):
        capacity = 64
        while capacity <= 1048576:
            data = C.create_string_buffer(8 + capacity * C.sizeof(SIZE))
            if query_job(self.job, 3, data, len(data), None):
                count = C.cast(data, C.POINTER(W.DWORD))[1]
                return list((SIZE * count).from_buffer(data, 8))
            if C.get_last_error() != 234:  # ERROR_MORE_DATA
                raise C.WinError(C.get_last_error())
            capacity *= 2
        raise RuntimeError('Owned process list exceeds monitoring capacity')

    def sample(self):
        rss = 0
        for pid in self.pids():
            handle = open_process(0x100000 | 0x410, False, pid)
            if not handle:
                if C.get_last_error() == 87:  # exited between enumeration and open
                    continue
                raise C.WinError(C.get_last_error())
            try:
                owned = W.BOOL()
                checked(is_in_job(handle, self.job, C.byref(owned)))
                if not owned.value or signaled(handle):
                    continue  # exited or PID reused outside this job
                memory = Memory()
                memory.cb = C.sizeof(memory)
                if not memory_info(handle, C.byref(memory), memory.cb):
                    if signaled(handle):
                        continue
                    raise C.WinError(C.get_last_error())
                rss += memory.WorkingSetSize
            finally:
                close_handle(handle)
        self.peak = max(self.peak, rss)
        info = self.accounting()
        return dict(rss_bytes=rss, peak_rss_bytes=self.peak,
                    cpu_seconds=(info.TotalUserTime + info.TotalKernelTime) / 1e7)

    def poll(self):
        if self.returncode is None and signaled(self.process):
            code = W.DWORD()
            checked(get_exit_code(self.process, C.byref(code)))
            self.returncode = code.value
        return self.returncode

    def running(self):
        # Job accounting can briefly still count a signaled/exited leader.
        # Inspect actual handles before calling anything a live descendant.
        if self.poll() is None:
            return True
        for pid in self.pids():
            if pid == self.pid:
                continue
            handle = open_process(0x100000 | 0x410, False, pid)
            if not handle:
                if C.get_last_error() == 87:
                    continue
                raise C.WinError(C.get_last_error())
            try:
                owned = W.BOOL()
                checked(is_in_job(handle, self.job, C.byref(owned)))
                if owned.value and not signaled(handle):
                    return True
            finally:
                close_handle(handle)
        return False

    def kill(self):
        checked(terminate_job(self.job, 125))

    def wait(self, timeout=5):
        deadline = time.monotonic() + timeout
        while self.running():
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired('owned Windows process cleanup', timeout)
            time.sleep(.01)
        return self.poll()

    def close(self):
        for name in ('job', 'thread', 'process'):
            handle = getattr(self, name, None)
            if handle:
                close_handle(handle)
                setattr(self, name, None)
