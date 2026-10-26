"""Create repeatable test projects without reading or writing the player's user data.

The baseline freezes scripts/tests; assets and Godot imports are shared read-only.
The candidate uses live scripts so captures and tests exercise the final revision.
"""
from pathlib import Path
import argparse
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "hero-port-20261026"


def junction(target, source):
    if not target.exists():
        quoted_target = "'" + str(target).replace("'", "''") + "'"
        quoted_source = "'" + str(source).replace("'", "''") + "'"
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"New-Item -ItemType Junction -Path {quoted_target} -Target {quoted_source} | Out-Null"],
                       check=True)


def prepare(label):
    source = ROOT / "game"
    project = OUT / (label + "-game")
    project.mkdir(parents=True, exist_ok=True)
    for name in ("src", "tests"):
        target = project / name
        if label == "baseline":
            if not target.exists():
                shutil.copytree(source / name, target)
        else:
            junction(target, source / name)
    for name in ("assets", ".godot"):
        if (source / name).exists():
            junction(project / name, source / name)
    for name in ("icon.svg", "icon.svg.import"):
        if (source / name).exists():
            shutil.copy2(source / name, project / name)
    config = (source / "project.godot").read_text(encoding="utf-8")
    config = config.replace('[application]', '[application]\n\nconfig/use_custom_user_dir=true\n'
                            'config/custom_user_dir_name="BeyondHeroesQA/hero-port-' + label + '"', 1)
    (project / "project.godot").write_text(config, encoding="utf-8")
    print(project)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label", choices=("baseline", "candidate"))
    prepare(parser.parse_args().label)
