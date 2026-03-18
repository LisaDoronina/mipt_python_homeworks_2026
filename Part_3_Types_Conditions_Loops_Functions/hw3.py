#!/usr/bin/env python

from datetime import date
from typing import NamedTuple

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be greater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
OP_SUCCESS_MSG = "Added"

MIN_MONTH = 1
MAX_MONTH = 12
FEBRUARY = 2

DATE_PARTS_EXPECTED = 3
INCOME_PARTS_EXPECTED = 3
COST_PARTS_EXPECTED = 4
STATS_PARTS_EXPECTED = 2

ZERO = 0

MONTH_DAYS = {
    1: 31,
    2: 28,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31,
}


class Stats(NamedTuple):
    total_capital: float
    month_income: float
    month_expenses: float
    categories: dict[str, float]


Income = tuple[float, date]
Expense = tuple[str, float, date]

incomes: list[Income] = []
expenses: list[Expense] = []


def is_leap_year(year: int) -> bool:
    if year % 4 != 0:
        return False

    if year % 100 != 0:
        return True

    return year % 400 == 0


def get_month_days(month: int, year: int) -> int:
    if month == FEBRUARY and is_leap_year(year):
        return 29

    return MONTH_DAYS[month]


def valid_date(date_obj: date | None) -> bool:
    if date_obj is None:
        return False

    day = date_obj.day
    month = date_obj.month
    year = date_obj.year

    if not (MIN_MONTH <= month <= MAX_MONTH and day >= MIN_MONTH and year >= MIN_MONTH):
        return False

    return day <= get_month_days(month, year)


def extract_date(date_str: str) -> date | None:
    parts = date_str.split("-")

    if len(parts) != DATE_PARTS_EXPECTED:
        return None

    day, month, year = parts

    if not (day.isdigit() and month.isdigit() and year.isdigit()):
        return None

    try:
        return date(int(year), int(month), int(day))
    except ValueError:
        return None


def parse_amount(amount: str) -> float | None:
    amount = amount.replace(",", ".")

    if amount.count(".") > 1:
        return None

    if not all(char.isdigit() or char == "." for char in amount):
        return None

    return float(amount)


def valid_amount(amount: float | None) -> bool:
    return amount is not None and amount > 0


def _capital_from_expenses(target_date: date) -> float:
    total = ZERO
    for _, amount, exp_date in expenses:
        if exp_date <= target_date:
            total -= amount
    return total


def _monthly_expense_data(target_date: date) -> tuple[float, dict[str, float]]:
    month_total = ZERO
    categories: dict[str, float] = {}

    for category, amount, exp_date in expenses:
        if exp_date.month == target_date.month and exp_date.year == target_date.year:
            month_total += amount
            categories[category] = categories.get(category, ZERO) + amount

    return month_total, categories


def _expense_totals(target_date: date) -> tuple[float, float, dict[str, float]]:
    capital = _capital_from_expenses(target_date)
    month_total, categories = _monthly_expense_data(target_date)
    return capital, month_total, categories


def _income_totals(target_date: date) -> tuple[float, float]:
    capital = ZERO
    month_income = ZERO

    for amount, inc_date in incomes:
        if inc_date <= target_date:
            capital += amount

        if inc_date.month == target_date.month and inc_date.year == target_date.year:
            month_income += amount

    return capital, month_income


def make_up_statistics(target_date: date) -> Stats:
    inc = _income_totals(target_date)
    exp = _expense_totals(target_date)

    total_capital = inc[0] - exp[0]

    return Stats(
        total_capital=total_capital,
        month_income=inc[1],
        month_expenses=exp[1],
        categories=exp[2],
    )


def print_breakdown(categories: dict[str, float]) -> None:
    if not categories:
        print()
        return

    for index, (category, amount) in enumerate(sorted(categories.items()), 1):
        print(f"{index}. {category}: {int(amount)}")


def format_delta_message(delta: float) -> str:
    if delta > 0:
        return f"This month's profit: {delta:.2f} rubles"
    return f"This month's loss: {abs(delta):.2f} rubles"


def print_stats(stats: Stats, date_str: str) -> None:
    categories = dict(stats.categories)

    print(f"Your statistics as of {date_str}:")
    print(f"Total capital: {stats.total_capital:.2f} rubles")

    delta = stats.month_income - stats.month_expenses
    print(format_delta_message(delta))

    print(f"Income: {stats.month_income:.2f} rubles")
    print(f"Expenses: {stats.month_expenses:.2f} rubles")
    print()
    print("Breakdown (category):")

    print_breakdown(categories)


def process_income(command_split: list[str]) -> None:
    if len(command_split) != INCOME_PARTS_EXPECTED:
        print(UNKNOWN_COMMAND_MSG)
        return

    amount_str, date_str = command_split[1:]
    amount = parse_amount(amount_str)
    parsed_date = extract_date(date_str)

    if parsed_date is None or not valid_date(parsed_date):
        print(INCORRECT_DATE_MSG)
        return

    if amount is None:
        print(UNKNOWN_COMMAND_MSG)
        return

    if not valid_amount(amount):
        print(NONPOSITIVE_VALUE_MSG)
        return

    incomes.append((amount, parsed_date))
    print(OP_SUCCESS_MSG)


def process_cost(command_split: list[str]) -> None:
    if len(command_split) != COST_PARTS_EXPECTED:
        print(UNKNOWN_COMMAND_MSG)
        return

    category, amount_str, date_str = command_split[1:]

    if not category or any(char in category for char in " .,"):
        print(UNKNOWN_COMMAND_MSG)
        return

    amount = parse_amount(amount_str)
    parsed_date = extract_date(date_str)

    if amount is None:
        print(UNKNOWN_COMMAND_MSG)
        return

    if not valid_amount(amount):
        print(NONPOSITIVE_VALUE_MSG)
        return

    if parsed_date is None or not valid_date(parsed_date):
        print(INCORRECT_DATE_MSG)
        return

    expenses.append((category, amount, parsed_date))
    print(OP_SUCCESS_MSG)


def process_stats(command_split: list[str]) -> None:
    if len(command_split) != STATS_PARTS_EXPECTED:
        print(UNKNOWN_COMMAND_MSG)
        return

    date_str = command_split[1]
    parsed_date = extract_date(date_str)

    if parsed_date is None or not valid_date(parsed_date):
        print(INCORRECT_DATE_MSG)
        return

    stats = make_up_statistics(parsed_date)
    print_stats(stats, date_str)


def main() -> None:
    command = input()
    command_split = command.split(" ")

    handlers = {
        "income": process_income,
        "cost": process_cost,
        "stats": process_stats,
    }

    handler = handlers.get(command_split[0])

    if handler is None:
        print(UNKNOWN_COMMAND_MSG)
        return

    handler(command_split)


if __name__ == "__main__":
    main()
