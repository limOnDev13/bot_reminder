"""
Модуль с реализацией бизнес-логики.
"""
from asyncpg import Record
from typing import List


def sort_notes_by_date(input_database: List[Record]):
    for i in range(len(input_database)):
        print(input_database[i])
