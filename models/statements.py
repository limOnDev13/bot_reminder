def st_insert_new_user(user_id: str) -> str:
    return f'INSERT INTO Users VALUES({user_id}, DEFAULT, DEFAULT);'

