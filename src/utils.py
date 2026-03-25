import re


def group_warnings(warnings: list[str]) -> dict[str, str | list[str]]:
    grouped: dict[str, str | list[str]] = {}
    pattern = r"^(.*?):\s*(.*)$"

    for warning in warnings:
        match = re.match(pattern, warning)
        if match:
            key, value = match.groups()
            if key in grouped:
                if isinstance(grouped[key], list):
                    grouped[key].append(value)
                else:
                    grouped[key] = [grouped[key], value]
            else:
                grouped[key] = value
        else:
            grouped[warning] = warning

    return grouped
