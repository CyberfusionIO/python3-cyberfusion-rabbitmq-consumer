#!/usr/bin/python3

"""Program to monitor rabbitmq-consumer units."""

import sys
from typing import List

from cyberfusion.Common.Systemd import CyberfusionUnits

PATTERN_NAME_UNIT_RABBITMQ_CONSUME = "rabbitmq-consume@*.service"


def main() -> None:
    """Spawn relevant class for CLI function."""  # noqa: D202

    # Set empty list

    inactive_units: List[str] = []

    # Loop through found units

    for unit in CyberfusionUnits().search(PATTERN_NAME_UNIT_RABBITMQ_CONSUME):
        # If active, skip

        if unit.get_is_active():
            continue

        # If not active, add to list

        inactive_units.append(unit.name)

    # Print critical and exit if not active

    if inactive_units:
        inactive_units_names = ", ".join(inactive_units)

        print(
            f"CRITICAL: Inactive units: {inactive_units_names}"
        )  # noqa: T001

        sys.exit(2)

    # Print OK and exit if active

    print("OK: No inactive units")

    sys.exit(0)


if __name__ == "__main__":
    main()
