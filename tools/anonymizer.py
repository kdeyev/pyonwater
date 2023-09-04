"""Simple JSON anonymization tool."""
import json
import os
import re
import sys
from typing import Any


def traverse(data: Any) -> Any:
    """Anonymize an entity"""
    if isinstance(data, dict):
        for k in data:
            data[k] = traverse(data[k])
        return data
    elif isinstance(data, int):
        return int("1" * len(str(data)))
    elif isinstance(data, float):
        return 42.0
    elif isinstance(data, str):
        data = re.sub(r"[a-zA-Z]", "X", data)
        data = re.sub(r"[\d]", "1", data)
        return data
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i] = traverse(data[i])
        return data
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
        output_filename = f"{filename}_anonymized.{file_extension}"

        with open(output_filename, "w") as f:
            json.dump(data, f, indent=True)

        print("Anonymized", output_filename, "created")


if __name__ == "__main__":
    main(sys.argv)
