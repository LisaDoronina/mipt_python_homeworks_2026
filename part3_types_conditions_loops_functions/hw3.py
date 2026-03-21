#!/usr/bin/env python

from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

financial_transactions_storage: list[dict[str, Any]] = []

incomes = []
expenses = []

EXPENSE_CATEGORIES = (
    ("Food", ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery")),
    ("Transport", ("Taxi", "Public transport", "Gas", "Car service")),
    ("Housing", ("Rent", "Utilities", "Repairs", "Furniture")),
    ("Health", ("Pharmacy", "Doctors", "Dentist", "Lab tests")),
    ("Entertainment", ("Movies", "Concerts", "Games", "Subscriptions")),
    ("Clothing", ("Outerwear", "Casual", "Shoes", "Accessories")),
    ("Education", ("Courses", "Books", "Tutors")),
    ("Communications", ("Mobile", "Internet", "Subscriptions")),
    ("Other", ()),
)

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

def is_leap_year(year):
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def get_subcategories(parent):
    for p, subs in EXPENSE_CATEGORIES:
        if p == parent:
            return subs
    return ()


def validate_category(category_str):
    if "::" not in category_str or not category_str:
        return None

    parent, sub = category_str.split("::", 1)

    if not parent or not sub or " " in parent or " " in sub:
        return None

    for item in EXPENSE_CATEGORIES:
        if item[0] == parent:
            if sub in item[1]:
                return parent, sub
            return None

    return None


def extract_date(maybe_dt):
    date = maybe_dt.split("-")

    if len(date) != DATE_SPLIT_LENGTH:
        return None

    day, month, year = date

    if not (day.isdigit() and month.isdigit() and year.isdigit()):
        return None

    return int(day), int(month), int(year)


def valid_date(date):
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


def parse_amount(amount):
    amount = amount.replace(",", ".")

    if amount.count(".") > 1:
        return None

    for char in amount:
        if not (char.isdigit() or char == "."):
            return None

    return float(amount)


def valid_amount(amount):
    if amount is None:
        return False
    return amount > 0


def get_all_categories():
    categories = []
    for parent, subs in EXPENSE_CATEGORIES.items():
        categories.extend([f"{parent}::{sub}" for sub in subs])
    return "\n".join(categories)


def compare_years(trans_date, target_date):
    if trans_date[2] != target_date[2]:
        return trans_date[2] < target_date[2]
    return None


def compare_months(trans_date, target_date):
    if trans_date[1] != target_date[1]:
        return trans_date[1] < target_date[1]
    return None


def is_before_or_on(trans_date, target_date):
    year_cmp = compare_years(trans_date, target_date)
    if year_cmp is not None:
        return year_cmp

    month_cmp = compare_months(trans_date, target_date)
    if month_cmp is not None:
        return month_cmp

    return trans_date[0] <= target_date[0]


def is_same_month_year(date1, date2):
    return (date1[2] == date2[2]
            and date1[1] == date2[1])


def calculate_income(target):
    capital = 0
    month_income = 0

    for inc in incomes:
        if is_before_or_on(inc[1], target):
            capital += inc[0]
            if is_same_month_year(inc[1], target):
                month_income += inc[0]

    return capital, month_income


def calculate_expenses(target):
    capital = 0
    month_expenses = 0
    categories = {}

    for exp in expenses:
        if is_before_or_on(exp[2], target):
            capital -= exp[1]
            if is_same_month_year(exp[2], target):
                month_expenses += exp[1]
                cat = exp[0]
                categories[cat] = categories.get(cat, 0) + exp[1]

    return capital, month_expenses, categories


def process_transactions(target_date):
    inc_capital, month_income = calculate_income(target_date)
    exp_capital, month_expenses, categories = calculate_expenses(target_date)
    return inc_capital + exp_capital, month_income, month_expenses, categories


def make_up_statistics(date):
    return list(process_transactions(date))


def print_stats(stats, date):
    print(f"Your statistics as of {date}:")
    print(f"Total capital: {stats[0]:.2f} rubles")

    if stats[1] > stats[2]:
        profit = stats[1] - stats[2]
        print(f"This month, the profit amounted to {profit:.2f} rubles.")
    else:
        profit = stats[2] - stats[1]
        print(f"This month, the loss amounted to {profit:.2f} rubles.")

    print(f"Income: {stats[1]:.2f} rubles\nExpenses: {stats[2]:.2f} rubles")
    print()
    print("Details (category: amount):")

    if not stats[3]:
        print()
        return

    sorted_categories = sorted(stats[3].items())
    for idx, (category, amount) in enumerate(sorted_categories, 1):
        print(f"{idx}. {category}: {int(amount):,}")


def validate_cost_input(category, amount_str, date_str):
    category_parts = validate_category(category)
    if category_parts is None:
        print(NOT_EXISTS_CATEGORY)
        print(get_all_categories())
        return None

    amount = parse_amount(amount_str)
    if not valid_amount(amount):
        if amount is None:
            print(UNKNOWN_COMMAND_MSG)
        else:
            print(NONPOSITIVE_VALUE_MSG)
        return None

    date = extract_date(date_str)
    if not valid_date(date):
        print(INCORRECT_DATE_MSG)
        return None

    return category, amount, date


def income_handler(command_split):
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


def cost_handler(command_split):
    if len(command_split) == COST_ARGS_COUNT and command_split[1] == "categories":
        print(get_all_categories())
        return

    if len(command_split) != COST_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return

    category, amount_str, date_str = command_split[1:]
    result = validate_cost_input(category, amount_str, date_str)

    if result is not None:
        expenses.append(result)
        print(OP_SUCCESS_MSG)


def stats_handler(command_split):
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


def main():
    command = input()
    command_split = command.split(" ")

    if command_split[0] == "income":
        income_handler(command_split)
    elif command_split[0] == "cost":
        cost_handler(command_split)
    elif command_split[0] == "stats":
        stats_handler(command_split)
    else:
        print(UNKNOWN_COMMAND_MSG)


if __name__ == "__main__":
    main()
