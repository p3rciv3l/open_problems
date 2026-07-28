import argparse
import gzip
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
SOURCE = HERE / "tools" / "boundary_memory.c"
EXAMPLES = HERE / "examples"
METADATA = EXAMPLES / "boundary_memory_summary.json"


def compress(source: Path, destination: Path) -> dict[str, object]:
    data = source.read_bytes()
    with destination.open("wb") as output:
        with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as compressed:
            compressed.write(data)
    return {
        "states": len(data),
        "raw_bytes": len(data),
        "gzip_bytes": destination.stat().st_size,
        "raw_sha256": hashlib.sha256(data).hexdigest(),
        "gzip_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
    }


def generate(output_directory: Path) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    expected = json.loads(METADATA.read_text())
    with tempfile.TemporaryDirectory() as temporary:
        temporary_path = Path(temporary)
        executable = temporary_path / "boundary_memory"
        live = temporary_path / "live.bin"
        dead = temporary_path / "dead.bin"
        subprocess.run(
            ["cc", "-O3", str(SOURCE), "-o", str(executable)],
            check=True,
        )
        process = subprocess.run(
            [str(executable), "generate", str(live), str(dead)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [str(executable), "verify", str(live), str(dead)],
            check=True,
        )
        actual = {
            "center_alive": compress(
                live, output_directory / "boundary_memory_live.bin.gz"
            ),
            "center_dead": compress(
                dead, output_directory / "boundary_memory_dead.bin.gz"
            ),
        }
        if process.stdout.strip().splitlines() != expected["generator_output"]:
            raise RuntimeError("generator summary does not match checked metadata")
        for key, metadata in actual.items():
            if metadata != expected[key]:
                raise RuntimeError(f"{key} certificate does not match checked metadata")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    if arguments.output:
        generate(arguments.output)
    else:
        with tempfile.TemporaryDirectory() as temporary:
            generate(Path(temporary))


if __name__ == "__main__":
    main()
