from typing import Any


class WrongTypeException(Exception):
    def __init__(self, object: Any, expected: str, given: str):
        self.message = f'Expected type: {expected}. Got: {given}. Object: {object}'
        super().__init__(self.message)

class NotImplementedTypeException(Exception):
    def __init__(self, object, obj_type):
        self.message = f'object {object} of type {obj_type} is not supported' \
                       f' in this function'
        super().__init__(self.message)