#!/usr/bin/env python

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

Income = tuple[float, tuple[int, int, int]]
Expense = tuple[str, float, tuple[int, int, int]]
DateTriple = tuple[int, int, int]
Stats = list[float | dict[str, float]]

incomes: list[Income] = []
expenses: list[Expense] = []


def is_leap_year(year: int) -> bool:
    if year % 4 != 0:
        return False
    if year % 100 != 0:
        return True
    if year % 400 != 0:
        return False
    return True


def valid_date(date: DateTriple | None) -> bool:
    if date is None:
        return False

    day, month, year = date

    if month < MIN_MONTH or month > MAX_MONTH or day < MIN_MONTH or year < MIN_MONTH:
        return False

    month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    if month == FEBRUARY and is_leap_year(year):
        return day <= LEAP_YEAR_DAY_LIMIT
    if month == FEBRUARY:
        return day <= NON_LEAP_YEAR_DAY_LIMIT

    return day <= month_days[month - MIN_MONTH]


def extract_date(maybe_dt: str) -> DateTriple | None:
    date = maybe_dt.split("-")

    if len(date) != DATE_PARTS_EXPECTED:
        return None

    day, month, year = date

    if not (day.isdigit() and month.isdigit() and year.isdigit()):
        return None

    return int(day), int(month), int(year)


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


def process_incomes(target_date: DateTriple) -> tuple[float, float]:
    day, month, year = target_date
    capital = 0.0
    month_income = 0.0

    for inc_amount, (inc_day, inc_month, inc_year) in incomes:
        if inc_year < year:
            capital += inc_amount
        elif inc_year == year and inc_month < month:
            capital += inc_amount
        elif inc_month == month and inc_day <= day:
            capital += inc_amount

        if inc_month == month and inc_year == year:
            month_income += inc_amount

    return capital, month_income


def process_expenses(target_date: DateTriple) -> tuple[float, float, dict[str, float]]:

    day, month, year = target_date
    capital = 0.0
    month_expenses = 0.0
    categories: dict[str, float] = {}

    for exp_category, exp_amount, (exp_day, exp_month, exp_year) in expenses:
        if exp_year < year:
            capital -= exp_amount
        elif exp_year == year and exp_month < month:
            capital -= exp_amount
        elif exp_month == month and exp_day <= day:
            capital -= exp_amount

        if exp_month == month and exp_year == year:
            month_expenses += exp_amount
            categories[exp_category] = categories.get(exp_category, 0) + exp_amount

    return capital, month_expenses, categories


def make_up_statistics(date: DateTriple) -> Stats:
    inc_capital, month_income = process_incomes(date)
    exp_capital, month_expenses, categories = process_expenses(date)

    total_capital = inc_capital - exp_capital

    return [total_capital, month_income, month_expenses, categories]


def print_breakdown(categories: dict[str, float]) -> None:
    if not categories:
        print()
        return

    for i, (category, amount) in enumerate(sorted(categories.items()), 1):
        print(f"{i}. {category}: {int(amount)}")


def print_stats(stats: Stats, date: str) -> None:
    categories = stats[3]

    print(f"Your statistics as of {date}:")
    print(f"Total capital: {stats[0]:.2f} rubles")

    delta = stats[1] - stats[2]

    if delta > 0:
        profit_msg = f"This month's profit: {delta:.2f} rubles"
        print(profit_msg)
    else:
        loss_msg = f"This month's loss: {-delta:.2f} rubles"
        print(loss_msg)

    print(f"Income: {stats[1]:.2f} rubles")
    print(f"Expenses: {stats[2]:.2f} rubles")
    print()
    print("Breakdown (category: amount):")

    print_breakdown(categories)


def process_income(command_split: list[str]) -> None:
    if len(command_split) != INCOME_PARTS_EXPECTED:
        print(UNKNOWN_COMMAND_MSG)
        return

    amount_str, date_str = command_split[1:]
    amount = parse_amount(amount_str)
    date = extract_date(date_str)

    if not valid_date(date):
        print(INCORRECT_DATE_MSG)
        return

    if not valid_amount(amount):
        print(UNKNOWN_COMMAND_MSG if amount is None else NONPOSITIVE_VALUE_MSG)
        return

    incomes.append((amount, date))
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
    date = extract_date(date_str)

    if not valid_amount(amount):
        print(UNKNOWN_COMMAND_MSG if amount is None else NONPOSITIVE_VALUE_MSG)
        return

    if not valid_date(date):
        print(INCORRECT_DATE_MSG)
        return

    expenses.append((category, amount, date))
    print(OP_SUCCESS_MSG)


def process_stats(command_split: list[str]) -> None:
    if len(command_split) != STATS_PARTS_EXPECTED:
        print(UNKNOWN_COMMAND_MSG)
        return

    date_str = command_split[1]
    date_extr = extract_date(date_str)

    if not valid_date(date_extr):
        print(INCORRECT_DATE_MSG)
        return

    stats = make_up_statistics(date_extr)
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