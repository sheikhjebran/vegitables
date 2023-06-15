import random

existing_numbers = set()


def generate_unique_number(min_value=1, max_value=10000):
    global existing_numbers
    while True:
        number = random.randint(min_value, max_value)
        if number not in existing_numbers:
            existing_numbers.add(number)
            return number
