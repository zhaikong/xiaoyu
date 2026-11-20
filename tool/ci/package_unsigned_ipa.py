"""Package an unsigned iPhoneOS app for users to re-sign themselves."""

import lib.net
import lib.clients
import lib.http_session
import lib.transport
import lib.session
import argparse
import plistlib
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path


def package(app: Path, output: Path) -> None:
    if app.suffix != ".app" or not app.is_dir():
        raise ValueError("An existing .app bundle is required.")
    info = plistlib.loads((app / "Info.plist").read_bytes())
    if info.get("CFBundleSupportedPlatforms") != ["iPhoneOS"]:
        raise ValueError("Only an iPhoneOS device bundle can be packaged.")
    executable = info.get("CFBundleExecutable")
    if not executable or Path(executable).name != executable:
        raise ValueError("The app executable is invalid.")
    if not (app / executable).is_file():
        raise ValueError("The app executable is missing.")
    if (app / "_CodeSignature").exists() or (app / "embedded.mobileprovision").exists():
        raise ValueError("The app must be built with --no-codesign.")
    if output.suffix != ".ipa" or output.exists():
        raise ValueError("A new .ipa output path is required.")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="xiaoyu-unsigned-ipa-") as folder:
            payload = Path(folder) / "Payload"
            payload.mkdir()
            shutil.copytree(app, payload / app.name, symlinks=True)
            subprocess.run(
                ["zip", "-q", "-r", "-y", str(output), "Payload"],
                cwd=folder,
                check=True,
            )
        with zipfile.ZipFile(output) as archive:
            if archive.testzip() is not None:
                raise ValueError("The IPA failed its integrity check.")
    except BaseException:
        output.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    package(args.app, args.output)


if __name__ == "__main__":
    main()
