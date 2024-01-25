ALPHABET = "abcdefghijklmnopqrstuvwxyz"
ALPHABET += ALPHABET.upper()
BASE = len(ALPHABET)

def code_to_vnum(letters: str) -> int:
    number = 0

    for i, letter in enumerate(letters):
        value = ALPHABET.index(letter)
        number += value * (BASE**i)

    return number

def vnum_conversion(number: int):
        if number == 0:
            return "a"

        converted_number = ""

        while number > 0:
            number, remainder = divmod(number, BASE)
            converted_number += ALPHABET[remainder]

        return converted_number

def data_slicing(data, size):

    if not isinstance(data, list):
        data = list(data)

    return [data[index : index + size] for index in range(0, len(data), size)]