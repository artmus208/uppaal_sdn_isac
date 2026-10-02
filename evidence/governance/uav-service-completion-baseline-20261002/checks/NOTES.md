# Retained check history

All checks are static validation or software tests. No new native UPPAAL run.

The first proposal-generation attempt referenced a nonexistent historical
n1/inventory.json and exited 1; corrected to the actual three required historical
files. The first proposal-control run had 11 successful tests and one fixture error
(KeyError model_hash): old PR81 provenance stores its model hash in the hashes map,
while result.json stores it directly. The corrected control uses real sim001 result
and provenance and all 12 controls pass. These were development defects in this
new package, not changed scientific inputs or successful verification.

The first repository suite in sandbox ran 209 tests and returned 1: one MCP stdio
startup timeout plus two console-entrypoint setup failures. The targeted six MCP
startup tests outside sandbox returned 0. An initial full outside retry ran 209 tests
and returned 1 solely because the isolated environment had no installed CLI.
The first offline install returned 2 because setuptools was missing. Cached
setuptools 82.0.1 and wheel 0.46.3 enabled installation from an exact source copy in
/tmp/uppaal84-install; the original checkout source paths were not modified.
The final installed-outside full suite ran 209 tests, no skips, and returned 0.
Every initial/retry log remains separately named and hash-pinned in check-results.json.

The original checkout .git is read-only in sandbox; the first git fetch returned
that error. The isolated clone's canonical SSH fetch failed DNS resolution. Exact
published base/candidate metadata and independent review were checked through the
GitHub connector, and local immutable Git blobs were compared directly. Original
execution Git history was imported from the owner's complete saved candidate bundle
into the isolated clone; the source-history audit checks every selected archived
input against its actual execution commit tree. Publication uses the canonical
GitHub connector when available, with the full bundle as an independent durable
backup. Current Git checkout/model/query/manifests were never repinned silently.

Environment setup used a separate venv and read-only existing MCP dependencies;
no fresh network dependency resolution was possible. Historical tool version and
license observations come from captured Engine.getVersion/raw responses. The
native version/license smoke in general CONTRIBUTING is intentionally not repeated
because this assignment explicitly prohibits new UPPAAL execution.
