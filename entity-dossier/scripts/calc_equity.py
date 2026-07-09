#!/usr/bin/env python3
"""Calculate direct and indirect shareholding percentages."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal, ROUND_HALF_UP, getcontext

getcontext().prec = 28


def percent(value: str) -> Decimal:
    return Decimal(value.strip().rstrip("%"))


def quantize(value: Decimal, places: int) -> Decimal:
    step = Decimal("1").scaleb(-places)
    return value.quantize(step, rounding=ROUND_HALF_UP)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Calculate a person's total holding. Indirect paths use "
            "label:person_owns_vehicle_percent:vehicle_owns_target_percent."
        )
    )
    parser.add_argument("--direct", default="0", help="Direct holding percentage.")
    parser.add_argument(
        "--indirect",
        action="append",
        default=[],
        help="Indirect path, e.g. 上海沐锐恒:40.3:25.1748",
    )
    parser.add_argument("--places", type=int, default=4, help="Decimal places.")
    args = parser.parse_args()

    direct = percent(args.direct)
    paths = []
    total_indirect = Decimal("0")

    for raw in args.indirect:
        try:
            label, holder_share, vehicle_share = raw.split(":", 2)
        except ValueError as exc:
            raise SystemExit(
                f"Invalid --indirect value {raw!r}; expected label:holder_share:vehicle_share"
            ) from exc

        holder = percent(holder_share)
        vehicle = percent(vehicle_share)
        contribution = holder * vehicle / Decimal("100")
        total_indirect += contribution
        paths.append(
            {
                "label": label,
                "holder_share_percent": str(quantize(holder, args.places)),
                "vehicle_target_share_percent": str(quantize(vehicle, args.places)),
                "contribution_percent": str(quantize(contribution, args.places)),
                "formula": f"{holder}% × {vehicle}% / 100",
            }
        )

    total = direct + total_indirect
    result = {
        "direct_percent": str(quantize(direct, args.places)),
        "indirect_percent": str(quantize(total_indirect, args.places)),
        "total_percent": str(quantize(total, args.places)),
        "paths": paths,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
