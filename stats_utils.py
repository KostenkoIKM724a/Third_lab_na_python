"""Допоміжні функції для обробки показників розумного будинку (ЛР №3)."""

import statistics
from collections.abc import Mapping, Sequence


def get_average(values: Sequence[float]) -> float | None:
    """Повертає середнє значення, округлене до двох знаків."""
    return round(float(statistics.mean(values)), 2) if values else None


def get_min(values: Sequence[float]) -> float | None:
    """Повертає мінімальне значення або None для порожнього набору."""
    return float(min(values)) if values else None


def get_max(values: Sequence[float]) -> float | None:
    """Повертає максимальне значення або None для порожнього набору."""
    return float(max(values)) if values else None


def get_median(values: Sequence[float]) -> float | None:
    """Повертає медіану, округлену до двох знаків."""
    return round(float(statistics.median(values)), 2) if values else None


def detect_jumps(
    values: Sequence[float], timestamps: Sequence[str], threshold: float
) -> list[str]:
    """Часові мітки ПІСЛЯ змін, модуль яких строго більший за поріг."""
    if len(values) != len(timestamps):
        raise ValueError("Кількості значень і часових міток не збігаються")
    if threshold < 0:
        raise ValueError("Поріг не може бути від'ємним")
    return [
        timestamps[i]
        for i in range(1, len(values))
        if abs(values[i] - values[i - 1]) > threshold
    ]


def print_table(parameter_name: str, data_dict: Mapping[str, float]) -> None:
    """Друкує таблицю початкових вимірювань у консолі."""
    heading = "Timestamp"
    date_width = max(len(heading), *(len(t) for t in data_dict))
    value_width = max(len(parameter_name), *(len(str(v)) for v in data_dict.values()))
    line = "+-" + "-" * date_width + "-+-" + "-" * value_width + "-+"
    print(f"\nПоказники для параметра: {parameter_name}")
    print(line)
    print(f"| {heading:<{date_width}} | {parameter_name:<{value_width}} |")
    print(line)
    for timestamp, value in data_dict.items():
        print(f"| {timestamp:<{date_width}} | {value!s:<{value_width}} |")
    print(line)


def print_statistics(parameter_name: str, result: Mapping[str, float | list[str]]) -> None:
    """Друкує підсумкові статистичні показники вибраного датчика."""
    print(f"\nСтатистика: {parameter_name}")
    for name, value in result.items():
        if name == "jumps":
            print(f"  {name}: {', '.join(value) if value else 'не знайдено'}")
        else:
            print(f"  {name}: {value}")
