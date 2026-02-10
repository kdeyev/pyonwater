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
        result: dict[Any, Any] = {}
        for k in data:  # type: ignore[var-annotated]
            result[k] = traverse(data[k])
        return result
    if isinstance(data, list):
        result_list: list[Any] = []
        for item in data:  # type: ignore[var-annotated]
            result_list.append(traverse(item))
        return result_list
    if isinstance(data, bool):
        return data
    if isinstance(data, int):
        return int("1" * len(str(data)))
    if isinstance(data, float):
        return 42.0
    if isinstance(data, str):
        if is_date(data, "%Y-%m-%dT%H:%M:%S.%fZ"):
            return datetime.datetime(1990, 1, 27, 0, 0).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ",
            )
        if is_date(data, "%Y-%m-%dT%H:%M:%S"):
            return datetime.datetime(1990, 1, 27, 0, 0).strftime("%Y-%m-%dT%H:%M:%S")
        if is_date(data, "%Y-%m-%d %H:%M:%S"):
            return datetime.datetime(1990, 1, 27, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
        if is_unit(data):
            return data
        data = re.sub(r"[a-zA-Z]", "X", data)
        return re.sub(r"[\d]", "1", data)
    return data


def main(argv: Any) -> None:
    """Main."""
    input_path = argv[1]

    print("Input", input_path)
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)
        data = traverse(data)
        filename, file_extension = os.path.splitext(input_path)
        output_filename = f"{filename}_anonymized{file_extension}"

        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=True)

        print("Anonymized", output_filename, "created")


if __name__ == "__main__":
    main(sys.argv)
