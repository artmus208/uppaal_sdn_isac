Initial run used a Python 3.11 environment installed for a different worktree.
209 tests: 3 failures, 4 errors, 2 skipped. Raw outputs are retained.
The stdio child did not inherit PYTHONPATH and loaded the older UI editable
package, exposing eight extra tools; that smoke result is environment-confounded.
Two errors were default cp1251 decoding. A clean task-specific Python 3.12
environment with MCP 1.30.0, PyYAML 6.0.2 and PYTHONUTF8=1 is used for the final
run. Source package is linked by a .pth entry to this worktree's src.
The initial scoped byte-gate control encountered missing query input before
the changed model hash was tested. check.py now rejects the model hash first;
the initial failing log is retained rather than overwritten.
