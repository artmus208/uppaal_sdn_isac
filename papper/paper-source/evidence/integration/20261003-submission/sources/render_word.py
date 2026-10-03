"""Run the skill renderer; tolerate Windows updater's temporary-file lock only.

The renderer's conversion and rasterization errors are not suppressed. A
TemporaryDirectory cleanup failure must not discard already rendered pages.
"""
import os,sys,runpy,tempfile
from pathlib import Path
original=tempfile.TemporaryDirectory
class WindowsTemporaryDirectory(original):
    def __init__(self,*args,**kwargs):
        kwargs['ignore_cleanup_errors']=True
        super().__init__(*args,**kwargs)
tempfile.TemporaryDirectory=WindowsTemporaryDirectory
os.environ['PATH']=r'D:\LibreOffice\program;D:\MikTeX\miktex\bin\x64;'+os.environ['PATH']
renderer=Path(os.environ['USERPROFILE'])/'.codex/plugins/cache/openai-primary-runtime/documents/26.909.12148/skills/documents/render_docx.py'
sys.argv=[str(renderer),*sys.argv[1:]]
runpy.run_path(str(renderer),run_name='__main__')
