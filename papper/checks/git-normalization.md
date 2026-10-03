# Git stat-cache repair, 2026-10-03

The initial clone used inherited `core.autocrlf=true`. After archive extraction
restored exact LF bytes and local autocrlf was disabled, the index still cached
the earlier CRLF file sizes. Example: `.github/CODEOWNERS` cached 266 bytes,
actual/HEAD 259 (7 LF characters); candidate `model.xml` cached 427646 bytes,
actual/HEAD 419521 (8125 LF characters). Both raw Git blob hashes match HEAD.
Git 2.35.1 treats a nonzero cached size mismatch as changed without content
hashing during refresh; therefore status can show M while a content diff is empty.
See [read-cache.c, ie_modified](https://github.com/git/git/blob/v2.35.1/read-cache.c#L407-L443).

The lead agent explicitly authorized refreshing only tracked files whose current
Git blob hash equals their existing index OID. The repair compared all candidate
blobs, excluded real changes, rechecked each batch immediately before `git add --`
with explicit paths, and required byte-identical `git ls-files --stage -z` output
before/after. SHA256 of every refreshed working file was also identical. No
source bytes, ACLs, Git config, credentials or branch refs were changed.

```json
{
  "tracked_status_before": 2095,
  "candidates": 2095,
  "stat_entries_refreshed": 2094,
  "excluded_real_changes": [
    "levels_tex/samplepaper.tex"
  ],
  "index_modes_oids_stages_paths_unchanged": true,
  "source_sha256_unchanged_for_all_refreshed": true,
  "tracked_status_after": [
    " M levels_tex/samplepaper.tex"
  ],
  "unstaged_numstat": "186\t202\tlevels_tex/samplepaper.tex\n",
  "staged_numstat": ""
}
```

Compact equivalent of the controlled operation (only after hashing the candidates):

```python
# original maps each stage-0 tracked path to its existing index OID.
# candidates come from git diff-files --name-only -z.
unchanged = [p for p in candidates if git_hash_object(p) == original[p]]
# Recheck every batch immediately before adding explicit unchanged paths.
for batch in bounded_batches(unchanged):
    assert all(git_hash_object(p) == original[p] for p in batch)
    subprocess.run(["git", "add", "--", *batch], check=True)
assert git_ls_files_stage_z_after == git_ls_files_stage_z_before
assert refreshed_working_file_sha256_after == refreshed_working_file_sha256_before
```

Publication precheck: the GitHub connector authenticates as `vadimnbkg` and its
repository collaborator permission is `write`. Existing native Windows credential
metadata names `artmus208`; noninteractive credential lookup explicitly requesting
`vadimnbkg` returned no credential. No token was printed, no interactive login
started, and nothing was pushed. Connector publication is available under the
real authenticated identity; native Git author metadata alone does not determine
the transport identity.

The separately diagnosed Pandoc access issue is an ACL problem: the escalated
pip-created `build/tools/pypandoc` directory under this integration package has
protected ACL inheritance, owner `musta`, and allows only OWNER RIGHTS, SYSTEM
and Administrators. Its `files/pandoc.exe` inherits those rules; the sandbox
principal cannot read it. An escalated read succeeds. This does not explain the
tracked-file stat-cache mismatch, and no ACL was modified.
