import os


def _data(filename: str) -> str:
    file_path = os.path.join(
        os.path.dirname(__file__), "data", filename
    )
    with open(file_path, "r") as file:
        return file.read()
