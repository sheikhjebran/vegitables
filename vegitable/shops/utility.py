import random
import time

existing_numbers = set()


def generate_unique_number(min_value=1, max_value=10000):
    global existing_numbers
    while True:
        number = random.randint(min_value, max_value)
        if number not in existing_numbers:
            existing_numbers.add(number)
            return number


def consolidate_result_for_report(result: list):
    response = {}
    for single_entry in result:
        if single_entry.get('id') in response:
            consolidate_dict = response.get(single_entry.get('id'))
            if consolidate_dict.get('iteam_name') != single_entry.get('iteam_name'):
                consolidate_dict[
                    'iteam_name'] = f"{consolidate_dict.get('iteam_name')},{single_entry.get('iteam_name')}"
            consolidate_dict['bags'] = int(consolidate_dict.get('bags')) + int(single_entry.get('bags'))
            response[single_entry.get('id')] = consolidate_dict
        else:
            response[single_entry.get('id')] = single_entry
    format_response = []
    for key, value in response.items():
        format_response.append(value)
    return format_response


def get_epoch():
    return str(time.time()).split(".")[0]


def get_float_number(number):
    try:
        return float(number)
    except ValueError:
        return 0
