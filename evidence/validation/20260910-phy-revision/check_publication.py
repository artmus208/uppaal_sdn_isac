"""Audit exact report publication and patch reconstruction, without model checking."""

from pathlib import Path
import hashlib
import json
import re
import subprocess
import tempfile


PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
BASE = "4480f1087b93f48541a925590ae82ca86fa4b808"
SCOPE = "evidence/validation/20260910-phy-revision/"
EXPECTED = {
    "validation-report.md": "cabda2a06ef942f7d572a1bf8db8396f522ca2c86f60440d0357f678f2403b8b",
    "validation-report.before-phy-revision-20260910.md": "23d62e29254786ddb7e3091584da5df4f6a79946fb69f293e03cbb74dafd637c",
    "validation-report.phy-revision-20260910.patch": "28b8033e25816f758ea6f116ec27eb88f7df2b51490cdb97f6f51d46a26de460",
    "validation-report.phy-revision-20260910.json": "7e51be5a26bb98c9137404dc31a85b8b076ed5e416ae52bea27f3d8955e55e94",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main():
    hashes = {}
    for name, expected in EXPECTED.items():
        hashes[name] = hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest()
        require(hashes[name] == expected, f"Source snapshot hash mismatch: {name}")
    original = (PACKAGE / "validation-report.before-phy-revision-20260910.md").read_bytes()
    historical_path = "evidence/validation/20260907-p1/validation-report.md"
    require(original == git("show", f"{BASE}:{historical_path}"), "Backup differs from pinned P1")
    require(original == (ROOT / historical_path).read_bytes(), "Historical P1 changed in checkout")
    with tempfile.TemporaryDirectory(prefix="phy-report-patch-") as directory:
        target = Path(directory) / "validation-report.md"
        target.write_bytes(original)
        subprocess.run(["git", "apply", "--unsafe-paths", str(PACKAGE / "validation-report.phy-revision-20260910.patch")], cwd=directory, check=True)
        require(target.read_bytes() == (PACKAGE / "validation-report.md").read_bytes(), "Patch reconstruction differs")
    checked_links = []
    for name in ("validation-report.md", "README.md"):
        for link in re.findall(r"\]\(([^)]+)\)", (PACKAGE / name).read_text(encoding="utf-8")):
            if "://" in link or link.startswith("#"):
                continue
            path = link.split("#", 1)[0]
            require((PACKAGE / path).is_file(), f"Broken local link in {name}: {link}")
            checked_links.append({"document": name, "target": link})
    paths = set(git("diff", "--name-only", BASE, "--").decode().splitlines())
    paths.update(git("ls-files", "--others", "--exclude-standard").decode().splitlines())
    require(all(path.startswith(SCOPE) for path in paths), f"Out-of-scope changes: {sorted(paths)}")
    subprocess.run(["git", "diff", "--check", BASE], cwd=ROOT, check=True)
    print(json.dumps({"kind": "publication_integrity_audit", "base_commit": BASE,
                      "hashes": hashes, "patch_reconstruction": "exact",
                      "historical_P1": "unchanged", "local_links": checked_links,
                      "changed_paths": sorted(paths), "scope_check": "success",
                      "verification": "not_run", "scientific_acceptance": "not_claimed"}, indent=2))


if __name__ == "__main__":
    main()
