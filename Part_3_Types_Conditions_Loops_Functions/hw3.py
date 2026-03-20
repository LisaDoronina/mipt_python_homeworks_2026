#!/usr/bin/env python

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

incomes: list[tuple[float, tuple[int, int, int]]] = []
expenses: list[tuple[str, float, tuple[int, int, int]]] = []

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": (),
}

MONTHS_IN_YEAR = 12
DAYS_IN_JANUARY = 31
DAYS_IN_FEBRUARY_NORMAL = 28
DAYS_IN_FEBRUARY_LEAP = 29
DATE_SPLIT_LENGTH = 3
INCOME_ARGS_COUNT = 3
COST_ARGS_COUNT = 4
STATS_ARGS_COUNT = 2
FEBRUARY = 2

valid_days_in_month = [
    0,
    DAYS_IN_JANUARY,
    28,
    DAYS_IN_JANUARY,
    30,
    DAYS_IN_JANUARY,
    30,
    DAYS_IN_JANUARY,
    DAYS_IN_JANUARY,
    30,
    DAYS_IN_JANUARY,
    30,
    DAYS_IN_JANUARY,
]


def is_leap_year(year: int) -> bool:
    return year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)


def valid_date(date: tuple[int, int, int] | None) -> bool:
    if date is None:
        return False

    day, month, year = date

    if month < 1 or month > MONTHS_IN_YEAR or day < 1 or year < 1:
        return False

    if month == FEBRUARY:
        if is_leap_year(year):
            return day <= DAYS_IN_FEBRUARY_LEAP
        return day <= DAYS_IN_FEBRUARY_NORMAL

    return day <= valid_days_in_month[month]


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    date = maybe_dt.split("-")

    if len(date) != DATE_SPLIT_LENGTH:
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


def validate_category(category_str: str) -> tuple[str, str] | None:
    if "::" not in category_str:
        return None

    parent, sub = category_str.split("::", 1)

    if not parent or not sub:
        return None

    if " " in parent or " " in sub:
        return None

    if parent not in EXPENSE_CATEGORIES:
        return None

    if sub not in EXPENSE_CATEGORIES[parent]:
        return None

    return parent, sub


def get_all_categories() -> str:
    return "\n".join(f"{parent}::{sub}" for parent, subs in EXPENSE_CATEGORIES.items() for sub in subs)


def make_up_statistics(date: tuple[int, int, int]) -> list[float | dict[str, float]]:
    day, month, year = date
    capital: float = 0
    month_income: float = 0
    month_expenses: float = 0
    categories: dict[str, float] = {}

    for inc_amount, (inc_day, inc_month, inc_year) in incomes:
        if inc_year < year or (inc_year == year and inc_month < month) or (inc_month == month and inc_day <= day):
            capital += inc_amount

            if inc_month == month and inc_year == year:
                month_income += inc_amount

    for exp_category, exp_amount, (exp_day, exp_month, exp_year) in expenses:
        if exp_year < year or (exp_year == year and exp_month < month) or (exp_month == month and exp_day <= day):
            capital -= exp_amount

            if exp_month == month and exp_year == year:
                month_expenses += exp_amount
                categories[exp_category] = categories.get(exp_category, 0) + exp_amount

    return [capital, month_income, month_expenses, categories]


def format_amount(amount: float) -> str:
    if amount.is_integer():
        return f"{int(amount):,}".replace(",", " ")
    return f"{amount:,.2f}".replace(",", " ")


def print_stats(stats: list[float | dict[str, float]], date: str) -> None:
    categories = stats[3]

    print(f"Your statistics as of {date}:")
    print(f"Total capital: {stats[0]:.2f} rubles")

    delta = stats[1] - stats[2]

    if delta > 0:
        print(f"This month, the profit amounted to {delta:.2f} rubles.")
    else:
        print(f"This month, the loss amounted to {-delta:.2f} rubles.")
    print(f"Income: {stats[1]:.2f} rubles")
    print(f"Expenses: {stats[2]:.2f} rubles")
    print()
    print("Details (category: amount):")

    if len(categories) > 0:
        for i, (category, amount) in enumerate(sorted(categories.items()), 1):
            amount_int = int(amount)
            formatted_amount = f"{amount_int:,}"
            print(f"{i}. {category}: {formatted_amount}")
    else:
        print()


def handle_income(command_split: list[str]) -> None:
    if len(command_split) != INCOME_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return

    amount_str, date_str = command_split[1:]

    amount = parse_amount(amount_str)
    date = extract_date(date_str)

    if not valid_amount(amount):
        if amount is None:
            print(UNKNOWN_COMMAND_MSG)
        else:
            print(NONPOSITIVE_VALUE_MSG)
        return

    if not valid_date(date):
        print(INCORRECT_DATE_MSG)
        return

    incomes.append((amount, date))
    print(OP_SUCCESS_MSG)


def handle_cost(command_split: list[str]) -> None:
    if len(command_split) == COST_ARGS_COUNT and command_split[1] == "categories":
        print(get_all_categories())
        return

    if len(command_split) != COST_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return

    category, amount_str, date_str = command_split[1:]

    category_parts = validate_category(category)
    if category_parts is None:
        print(NOT_EXISTS_CATEGORY)
        print(get_all_categories())
        return

    amount = parse_amount(amount_str)
    date = extract_date(date_str)

    if not valid_amount(amount):
        if amount is None:
            print(UNKNOWN_COMMAND_MSG)
        else:
            print(NONPOSITIVE_VALUE_MSG)
        return

    if not valid_date(date):
        print(INCORRECT_DATE_MSG)
        return

    expenses.append((category, amount, date))
    print(OP_SUCCESS_MSG)


def handle_stats(command_split: list[str]) -> None:
    if len(command_split) != STATS_ARGS_COUNT:
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

    if command_split[0] == "income":
        handle_income(command_split)
    elif command_split[0] == "cost":
        handle_cost(command_split)
    elif command_split[0] == "stats":
        handle_stats(command_split)
    else:
        print(UNKNOWN_COMMAND_MSG)


if __name__ == "__main__":
    main()
