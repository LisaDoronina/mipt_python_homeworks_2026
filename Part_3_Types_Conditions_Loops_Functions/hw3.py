#!/usr/bin/env python
from datetime import date
from typing import cast

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be greater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
OP_SUCCESS_MSG = "Added"

MIN_MONTH = 1
MAX_MONTH = 12
FEBRUARY = 2
LEAP_YEAR_DAY_LIMIT = 29
NON_LEAP_YEAR_DAY_LIMIT = 28
DATE_PARTS_EXPECTED = 3
INCOME_PARTS_EXPECTED = 3
COST_PARTS_EXPECTED = 4
STATS_PARTS_EXPECTED = 2

JAN_DAYS = 31
FEB_DAYS = 28
MAR_DAYS = 31
APR_DAYS = 30
MAY_DAYS = 31
JUN_DAYS = 30
JUL_DAYS = 31
AUG_DAYS = 31
SEP_DAYS = 30
OCT_DAYS = 31
NOV_DAYS = 30
DEC_DAYS = 31

month_days_map = {
    1: JAN_DAYS,
    2: FEB_DAYS,
    3: MAR_DAYS,
    4: APR_DAYS,
    5: MAY_DAYS,
    6: JUN_DAYS,
    7: JUL_DAYS,
    8: AUG_DAYS,
    9: SEP_DAYS,
    10: OCT_DAYS,
    11: NOV_DAYS,
    12: DEC_DAYS,
}

Income = tuple[float, date]
Expense = tuple[str, float, date]
Stats = list[float | dict[str, float]]

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
        return LEAP_YEAR_DAY_LIMIT
    return month_days_map[month]


def valid_date(date_obj: date | None) -> bool:
    if date_obj is None:
        return False

    day, month, year = date_obj.day, date_obj.month, date_obj.year

    if month < MIN_MONTH or month > MAX_MONTH or day < MIN_MONTH or year < MIN_MONTH:
        return False

    max_days = get_month_days(month, year)
    return day <= max_days


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

    for char in amount:
        if not (char.isdigit() or char == "."):
            return None

    return float(amount)


def valid_amount(amount: float | None) -> bool:
    if amount is None:
        return False
    return amount > 0


def should_include_income(inc_date: date, target_date: date) -> bool:
    """Check if income date should be included (<= target date)."""
    return inc_date <= target_date


def should_include_expense(exp_date: date, target_date: date) -> bool:
    """Check if expense date should be included (<= target date)."""
    return exp_date <= target_date


def _capital_from_expenses(target_date: date) -> float:
    """Calculate capital impact from expenses."""
    total = 0
    for _, amount, exp_date in expenses:
        if should_include_expense(exp_date, target_date):
            total -= amount
    return float(total)


def _monthly_expense_data(target_date: date) -> tuple[float, dict[str, float]]:
    """Calculate monthly expense total and categories."""
    month_total = 0
    categories: dict[str, float] = {}

    for category, amount, exp_date in expenses:
        if exp_date.month == target_date.month and exp_date.year == target_date.year:
            month_total += amount
            current = categories.get(category, 0)
            categories[category] = current + amount

    return float(month_total), categories


def _calculate_expense_totals(
        target_date: date,
) -> tuple[float, float, dict[str, float]]:
    """Calculate expense totals and category breakdown."""
    capital = _capital_from_expenses(target_date)
    month_total, categories = _monthly_expense_data(target_date)
    return capital, month_total, categories


def _income_totals(target_date: date) -> tuple[float, float]:
    """Calculate income totals."""
    capital = 0
    month_income = 0

    for inc_amount, inc_date in incomes:
        if should_include_income(inc_date, target_date):
            capital += inc_amount

        if inc_date.month == target_date.month and inc_date.year == target_date.year:
            month_income += inc_amount

    return float(capital), float(month_income)


def make_up_statistics(target_date: date) -> Stats:
    """Calculate complete statistics for target date."""
    inc_capital, month_income = _income_totals(target_date)
    exp_capital, month_expenses, categories = _calculate_expense_totals(target_date)

    total_capital = inc_capital - exp_capital
    return [total_capital, month_income, month_expenses, categories]


def print_breakdown(categories: dict[str, float]) -> None:
    """Print expense breakdown by category."""
    if not categories:
        print()
        return

    for i, (category, amount) in enumerate(sorted(categories.items()), 1):
        print(f"{i}. {category}: {int(amount)}")


def _format_profit_message(delta: float) -> str:
    """Format profit message."""
    return f"This month's profit: {delta:.2f} rubles"


def _format_loss_message(delta: float) -> str:
    """Format loss message."""
    return f"This month's loss: {abs(delta):.2f} rubles"


def format_delta_message(delta: float) -> str:
    """Format profit/loss message based on delta value."""
    if delta > 0:
        return _format_profit_message(delta)
    return _format_loss_message(delta)


def print_stats(stats: Stats, date_str: str) -> None:
    """Print statistics."""
    # Cast to proper types for mypy
    total_capital = float(stats[0])
    month_income = float(stats[1])
    month_expenses = float(stats[2])
    categories = stats[3]

    # Ensure categories is a dict
    if not isinstance(categories, dict):
        categories = {}
    else:
        categories = dict(categories)

    print(f"Your statistics as of {date_str}:")
    print(f"Total capital: {total_capital:.2f} rubles")

    delta = month_income - month_expenses
    print(format_delta_message(delta))

    print(f"Income: {month_income:.2f} rubles")
    print(f"Expenses: {month_expenses:.2f} rubles")
    print()
    print("Breakdown (category):")

    print_breakdown(categories)


def process_income(command_split: list[str]) -> None:
    """Process income command."""
    if len(command_split) != INCOME_PARTS_EXPECTED:
        print(UNKNOWN_COMMAND_MSG)
        return

    amount_str, date_str = command_split[1:]
    parsed_amount = parse_amount(amount_str)
    parsed_date = extract_date(date_str)

    if parsed_date is None or not valid_date(parsed_date):
        print(INCORRECT_DATE_MSG)
        return

    if parsed_amount is None or not valid_amount(parsed_amount):
        print(UNKNOWN_COMMAND_MSG if parsed_amount is None else NONPOSITIVE_VALUE_MSG)
        return

    incomes.append((parsed_amount, parsed_date))
    print(OP_SUCCESS_MSG)


def process_cost(command_split: list[str]) -> None:
    """Process cost command."""
    if len(command_split) != COST_PARTS_EXPECTED:
        print(UNKNOWN_COMMAND_MSG)
        return

    category, amount_str, date_str = command_split[1:]

    if not category or " " in category or "." in category or "," in category:
        print(UNKNOWN_COMMAND_MSG)
        return

    parsed_amount = parse_amount(amount_str)
    parsed_date = extract_date(date_str)

    if parsed_amount is None or not valid_amount(parsed_amount):
        print(UNKNOWN_COMMAND_MSG if parsed_amount is None else NONPOSITIVE_VALUE_MSG)
        return

    if parsed_date is None or not valid_date(parsed_date):
        print(INCORRECT_DATE_MSG)
        return

    expenses.append((category, parsed_amount, parsed_date))
    print(OP_SUCCESS_MSG)


def process_stats(command_split: list[str]) -> None:
    """Process stats command."""
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
    """Main entry point."""
    command = input()
    command_split = command.split(" ")

    command_handlers = {
        "income": process_income,
        "cost": process_cost,
        "stats": process_stats,
    }

    handler = command_handlers.get(command_split[0])
    if handler:
        handler(command_split)
    else:
        print(UNKNOWN_COMMAND_MSG)


if __name__ == "__main__":
    main()
