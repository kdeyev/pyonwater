"""Simple JSON anonymization tool."""
import datetime
import json
import os
import re
import sys
from typing import Any

from pyonwater.models import EOWUnits


def is_date(string: str, mask: str) -> bool:
    """Verify is the string is pyonwater supported datetime."""
    try:
        datetime.datetime.strptime(string, mask)
        return True
    except ValueError:
        return False


def is_unit(string: str) -> bool:
    """Verify is the string is pyonwater supported measurement unit."""
    try:
        EOWUnits(string)
        return True
    except ValueError:
        return False


def traverse(data: Any) -> Any:  # noqa: C901
    """Anonymize an entity."""
    if isinstance(data, dict):
        for k in data:
            data[k] = traverse(data[k])
        return data
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i] = traverse(data[i])
        return data
    elif isinstance(data, bool):
        return data
    elif isinstance(data, int):
        return int("1" * len(str(data)))
    elif isinstance(data, float):
        return 42.0
    elif isinstance(data, str):
        if is_date(data, "%Y-%m-%dT%H:%M:%S.%fZ"):
            return datetime.datetime(1990, 1, 27, 0, 0).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ",
            )
        elif is_date(data, "%Y-%m-%dT%H:%M:%S"):
            return datetime.datetime(1990, 1, 27, 0, 0).strftime("%Y-%m-%dT%H:%M:%S")
        elif is_date(data, "%Y-%m-%d %H:%M:%S"):
            return datetime.datetime(1990, 1, 27, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
        elif is_unit(data):
            return data
        else:
            data = re.sub(r"[a-zA-Z]", "X", data)
            return re.sub(r"[\d]", "1", data)
    else:
        return data


def main(argv: Any) -> None:
    """Main."""
    input_path = argv[1]

    print("Input", input_path)
    with open(input_path) as f:
        data = json.load(f)
        data = traverse(data)
        filename, file_extension = os.path.splitext(input_path)
        output_filename = f"{filename}_anonymized{file_extension}"

        with open(output_filename, "w") as f:
            json.dump(data, f, indent=True)

        print("Anonymized", output_filename, "created")


if __name__ == "__main__":
    main(sys.argv)
