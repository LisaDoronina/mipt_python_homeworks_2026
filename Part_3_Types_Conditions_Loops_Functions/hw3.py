#!/usr/bin/env python
from datetime import date

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


def process_incomes(target_date: date) -> tuple[float, float]:
    capital = 0.0
    month_income = 0.0

    for inc_amount, inc_date in incomes:
        if should_include_income(inc_date, target_date):
            capital += inc_amount

        if inc_date.month == target_date.month and inc_date.year == target_date.year:
            month_income += inc_amount

    return capital, month_income


def process_expenses(target_date: date) -> tuple[float, float, dict[str, float]]:
    capital = 0.0
    month_expenses = 0.0
    categories: dict[str, float] = {}

    for exp_category, exp_amount, exp_date in expenses:
        if should_include_expense(exp_date, target_date):
            capital -= exp_amount

        if exp_date.month == target_date.month and exp_date.year == target_date.year:
            month_expenses += exp_amount
            categories[exp_category] = categories.get(exp_category, 0) + exp_amount

    return capital, month_expenses, categories


def make_up_statistics(target_date: date) -> Stats:
    inc_capital, month_income = process_incomes(target_date)
    exp_result = process_expenses(target_date)
    total_capital = inc_capital - exp_result[0]

    return [total_capital, month_income, exp_result[1], exp_result[2]]


def print_breakdown(categories: dict[str, float]) -> None:
    if not categories:
        print()
        return

    for i, (category, amount) in enumerate(sorted(categories.items()), 1):
        print(f"{i}. {category}: {int(amount)}")


def format_delta_message(delta: float) -> str:
    if delta > 0:
        return f"This month's profit: {delta:.2f} rubles"
    return f"This month's loss: {-delta:.2f} rubles"


def print_stats(stats: Stats, date_str: str) -> None:
    categories = stats[3]

    print(f"Your statistics as of {date_str}:")
    print(f"Total capital: {stats[0]:.2f} rubles")

    delta = stats[1] - stats[2]
    print(format_delta_message(delta))

    print(f"Income: {stats[1]:.2f} rubles")
    print(f"Expenses: {stats[2]:.2f} rubles")
    print()
    print("Breakdown (category):")

    print_breakdown(categories)


def process_income(command_split: list[str]) -> None:
    if len(command_split) != INCOME_PARTS_EXPECTED:
        print(UNKNOWN_COMMAND_MSG)
        return

    amount_str, date_str = command_split[1:]
    amount = parse_amount(amount_str)
    date_obj = extract_date(date_str)

    if not valid_date(date_obj):
        print(INCORRECT_DATE_MSG)
        return

    if not valid_amount(amount):
        print(UNKNOWN_COMMAND_MSG if amount is None else NONPOSITIVE_VALUE_MSG)
        return

    incomes.append((amount, date_obj))
    print(OP_SUCCESS_MSG)


def process_cost(command_split: list[str]) -> None:
    if len(command_split) != COST_PARTS_EXPECTED:
        print(UNKNOWN_COMMAND_MSG)
        return

    category, amount_str, date_str = command_split[1:]

    if not category or " " in category or "." in category or "," in category:
        print(UNKNOWN_COMMAND_MSG)
        return

    amount = parse_amount(amount_str)
    date_obj = extract_date(date_str)

    if not valid_amount(amount):
        print(UNKNOWN_COMMAND_MSG if amount is None else NONPOSITIVE_VALUE_MSG)
        return

    if not valid_date(date_obj):
        print(INCORRECT_DATE_MSG)
        return

    expenses.append((category, amount, date_obj))
    print(OP_SUCCESS_MSG)


def process_stats(command_split: list[str]) -> None:
    if len(command_split) != STATS_PARTS_EXPECTED:
        print(UNKNOWN_COMMAND_MSG)
        return

    date_str = command_split[1]
    date_obj = extract_date(date_str)

    if not valid_date(date_obj):
        print(INCORRECT_DATE_MSG)
        return

    stats = make_up_statistics(date_obj)
    print_stats(stats, date_str)


def main() -> None:
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
