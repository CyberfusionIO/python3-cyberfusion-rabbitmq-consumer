#!/usr/bin/python3

"""Program to monitor rabbitmq-consumer units."""

import sys
from typing import List

from cyberfusion.SystemdSupport import Systemd

PATTERN_NAME_UNIT_RABBITMQ_CONSUME = "rabbitmq-consume@*.service"


def main() -> None:
    """Spawn relevant class for CLI function."""  # noqa: D202

    # Set empty list

    failed_units: List[str] = []

    # Loop through found units

    for unit in Systemd().search_units(PATTERN_NAME_UNIT_RABBITMQ_CONSUME):
        # If active, skip

        if unit.is_failed:
            continue

        # If not active, add to list

        failed_units.append(unit.name)

    # Print critical and exit if not active

    if failed_units:
        failed_units_names = ", ".join(failed_units)

        print(f"CRITICAL: Failed units: {failed_units_names}")

        sys.exit(2)

    # Print OK and exit if active

    print("OK: No failed units")

    sys.exit(0)


if __name__ == "__main__":
    main()
