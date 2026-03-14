#!/usr/bin/env python

UNKNOWN_COMMAND_MSG = "Неизвестная команда!"
NONPOSITIVE_VALUE_MSG = "Значение должно быть больше нуля!"
INCORRECT_DATE_MSG = "Неправильная дата!"
OP_SUCCESS_MSG = "Добавлено"

incomes = []
expenses = []


def is_leap_year(year: int) -> bool:

    if year % 4 != 0:
        return False
    elif year % 100 != 0:
        return True
    elif year % 400 != 0:
        return False

    return True

def valid_date(date: tuple[int, int, int] | None) -> bool:

    if date is None:
        return False

    day, month, year = date

    if month < 1 or month > 12 or day < 1 or year < 1:
        return False

    valid_days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    if month == 2:
        if is_leap_year(year):
            return day <= 29
        else:
            return day <= 28

    return day <= valid_days_in_month[month - 1]

def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:

    date = maybe_dt.split("-")

    if len(date) != 3:
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

def valid_amount(amount: int | float | None) -> bool:
    if amount is None:
        return False
    return amount > 0

def make_up_statistics(date: tuple[int, int, int]) -> list:

    day, month, year = date
    capital = 0.0
    month_income = 0.0
    month_expenses = 0.0
    categories = {}

    for inc_amount, (inc_day, inc_month, inc_year) in incomes:
        if (inc_year < year or (inc_year == year and inc_month < month) or (inc_month == month and inc_day <= day)):
            capital += inc_amount

            if inc_month == month and inc_year == year:
                month_income += inc_amount

    for exp_category, exp_amount, (exp_day, exp_month, exp_year) in expenses:
        if (exp_year < year or (exp_year == year and exp_month < month) or (exp_month == month and exp_day <= day)):
            capital -= exp_amount

            if exp_month == month and exp_year == year:
                month_expenses += exp_amount
                categories[exp_category] = categories.get(exp_category, 0) + exp_amount

    return [capital, month_income, month_expenses, categories]



def print_stats(stats: list, date: str) -> None:
    categories = stats[3]

    print(f"Ваша статистика по состоянию на {date}:")
    print(f"Суммарный капитал: {stats[0]:.2f} рублей")

    delta = stats[1] - stats[2]

    if delta > 0:
        print(f"В этом месяце прибыль составила {delta:.2f} рублей")
    else:
        print(f"В этом месяце убыток составил {-delta:.2f} рублей")
    print(f"Доходы: {stats[1]:.2f} рублей")
    print(f"Расходы: {stats[2]:.2f} рублей")
    print()
    print("Детализация (категория: сумма):")

    if len(categories) > 0:
        for i, (category, amount) in enumerate(sorted(categories.items()), 1):
            print(f"{i}. {category}: {int(amount)}")
    else:
        print()




def main() -> None:

    command = input()
    command_split = command.split(" ")

    if command_split[0] == "income":
        if len(command_split) != 3:
            print(UNKNOWN_COMMAND_MSG)
            return

        amount, date = command_split[1:]

        amount = parse_amount(amount)
        date = extract_date(date)

        if not valid_date(date):
            print(INCORRECT_DATE_MSG)
            return

        if not valid_amount(amount):
            if amount is None:
                print(UNKNOWN_COMMAND_MSG)
            else:
                print(NONPOSITIVE_VALUE_MSG)
            return

        incomes.append((amount, date))
        print(OP_SUCCESS_MSG)

    elif command_split[0] == "cost":
        if len(command_split) != 4:
            print(UNKNOWN_COMMAND_MSG)
            return

        category, amount, date = command_split[1:]

        if not category or " " in category or "." in category or "," in category:
            print(UNKNOWN_COMMAND_MSG)
            return

        amount = parse_amount(amount)
        date = extract_date(date)

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

    elif command_split[0] == "stats":
        if len(command_split) != 2:
            print(UNKNOWN_COMMAND_MSG)
            return

        date = command_split[1]
        date_extr = extract_date(date)
        if not valid_date(date_extr):
            print(INCORRECT_DATE_MSG)
            return

        stats = make_up_statistics(date_extr)

        print_stats(stats, date)

    else:
        print(UNKNOWN_COMMAND_MSG)


if __name__ == "__main__":
    main()
