"""Command line entry point."""

from __future__ import annotations

import argparse
from typing import Sequence

from tankfarm.config.schema import DEFAULT_SETTINGS, ControlSettings
from tankfarm.console.server import ControlServer
from tankfarm.console.wiring import build_services


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="tankfarm", description="line control service")
    parser.add_argument("--addr", default="", help="listen address, host:port")
    parser.add_argument("--data", default="", help="data directory")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="deprecated: replay now always runs on start (kept for compatibility)",
    )
    parser.add_argument(
        "--no-resume",
        dest="resume_start",
        action="store_false",
        help="start from seed state without replaying the stored record stream",
    )
    parser.set_defaults(resume_start=True)
    return parser.parse_args(argv)


def settings_for(args: argparse.Namespace) -> ControlSettings:
    settings = DEFAULT_SETTINGS
    if args.addr:
        settings = settings.with_addr(args.addr)
    if args.data:
        settings = settings.with_data_dir(args.data)
    return settings


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    settings = settings_for(args)
    services = build_services(settings)
    if args.resume_start:
        services.restore()
    server = ControlServer(settings.addr, services)
    httpd = server.create()
    print(
        f"control service on {server.host}:{server.bound_port()} data={settings.data_dir}",
        flush=True,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        services.bus.close()
    return 0
