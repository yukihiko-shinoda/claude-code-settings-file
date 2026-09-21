from pathlib import Path
import argparse

from converter.converter import SettingsConverter


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert managed-settings.yaml to managed-settings.json.")
    parser.add_argument("source", nargs="?", type=Path, default=Path("managed-settings.yaml"))
    parser.add_argument("destination", nargs="?", type=Path, default=Path("managed-settings.json"))
    args = parser.parse_args()
    SettingsConverter(args.source, args.destination).convert()
