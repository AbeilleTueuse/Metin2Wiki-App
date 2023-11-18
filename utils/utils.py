def data_slicing(data, size):

    if not isinstance(data, list):
        data = list(data)

    return [data[index : index + size] for index in range(0, len(data), size)]