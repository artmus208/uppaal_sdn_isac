"""Index and check exact bytes of the delivered P2 package; not verification."""
import argparse
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX = HERE / "SHA256SUMS"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write-index", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write_index:
        files = sorted(p for p in HERE.rglob("*") if p.is_file() and p != INDEX and "__pycache__" not in p.parts)
        lines = [f"{digest(p)}  {p.relative_to(HERE).as_posix()}\n" for p in files]
        with INDEX.open("xb") as stream:
            stream.write("".join(lines).encode("utf-8"))
        print(f"Indexed {len(files)} package files; SHA256SUMS excluded from its own index.")
    else:
        count = 0
        for line in INDEX.read_text(encoding="utf-8").splitlines():
            expected, name = line.split("  ", 1)
            path = (HERE / name).resolve()
            if not path.is_relative_to(HERE) or digest(path) != expected:
                raise ValueError(f"package integrity mismatch: {name}")
            count += 1
        print(f"{count} indexed package hashes match exact file bytes. Not model checking.")


if __name__ == "__main__":
    main()
