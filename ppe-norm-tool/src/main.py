"""ppe-norm-tool — ХХХ норм хэрэглээ ба солилтын хяналтын CLI.

Ашиглах жишээ:
    python src/main.py forecast --reserve 0.1
    python src/main.py forecast --reserve 0.15 --site Өртөө
    python src/main.py replacement --asof 2026-07-08 --days 30
"""

from __future__ import annotations

import argparse
from pathlib import Path

import forecast
import replacement

ЭНД_БАЙРЛАХ = Path(__file__).resolve().parent.parent
DATA_DIR = ЭНД_БАЙРЛАХ / "data"
OUTPUT_DIR = ЭНД_БАЙРЛАХ / "output"


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ХХХ норм хэрэглээ ба солилтын хяналтын хэрэгсэл")
    sub = p.add_subparsers(dest="command", required=True)

    forecast_p = sub.add_parser("forecast", help="Жилийн норм хэрэглээ ба төсвийн тооцоо")
    forecast_p.add_argument("--reserve", type=float, default=0.1, help="Нөөцийн хувь (жишээ: 0.1 = 10%%)")
    forecast_p.add_argument("--site", type=str, default=None, help="Зөвхөн нэг талбайг тооцох (жишээ: Өртөө)")

    replacement_p = sub.add_parser("replacement", help="Ажилтан тус бүрийн солих хугацааны хяналт")
    replacement_p.add_argument("--asof", type=str, default=None, help="Хяналт хийх огноо (YYYY-MM-DD), өгөгдөөгүй бол өнөөдөр")
    replacement_p.add_argument("--days", type=int, default=30, help="Дуусахад үлдсэн хоногийн босго (default: 30)")

    return p


def main() -> None:
    args = _parser().parse_args()

    if args.command == "forecast":
        forecast.тооцоолол_хийх(
            data_dir=DATA_DIR,
            output_dir=OUTPUT_DIR,
            reserve=args.reserve,
            site=args.site,
        )
    elif args.command == "replacement":
        replacement.хяналт_хийх(
            data_dir=DATA_DIR,
            output_dir=OUTPUT_DIR,
            asof=args.asof,
            days=args.days,
        )


if __name__ == "__main__":
    main()
