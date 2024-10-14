import json

def load_symbols_from_json(file_path):
    """
    Load stock symbols from a JSON file.
    
    :param file_path: The path to the JSON file.
    :return: A list of stock symbols.
    """
    with open(file_path, "r") as file:
        data = json.loads(file.read())
        symbols = data.get("symbols", [])
        return symbols