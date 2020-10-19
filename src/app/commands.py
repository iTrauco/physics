from pymongo.database import Database
from telebot.types import Message
import pandas as pd

from app.db import DBS
from app.db.queries import UPDATE_USER_GROUP, START_GROUP_LESSON
from app.settings.consts import SUCCESSED_TEXT, ERROR_PARSE_MESSAGE, DEBUG, SEARCH_NOT_FOUND_TEXT
from app.utils.command_parse import parse_group_name, parse_student_substring
from app.utils.gtables import parse_gtable


def new_group_command(message: Message):
    group_name = parse_group_name(message.text)
    if not group_name:
        return ERROR_PARSE_MESSAGE

    db: Database = DBS['mongo']['client']

    db.get_collection('users').update_one(
        UPDATE_USER_GROUP(
            user_id=message.from_user.id,
            group_name=group_name),
        upsert=True)

    db.get_collection('users_tables').update_one(
        START_GROUP_LESSON(
            user_id=message.from_user.id,
            group_name=group_name),
        upsert=True)
    return SUCCESSED_TEXT


def start_lesson_command(message: Message):
    user_table = parse_group_name(message.text)
    db: Database = DBS['mongo']['client']
    user = db.get_collection('users').find_one({
        '_id': message.from_user.id
    })

    db.get_collection('users').update_one(
        UPDATE_USER_GROUP(
            user_id=message.from_user.id,
            group_name=user_table),
        upsert=True)

    db.get_collection('users_tables').update_one(
        START_GROUP_LESSON(
            user_id=message.from_user.id,
            group_name=user_table),
        upsert=True)
    return SUCCESSED_TEXT


def search_command(message: Message):
    student_substr = parse_student_substring(message.text)
    if not student_substr:
        return ERROR_PARSE_MESSAGE

    db: Database = DBS['mongo']['client']
    user = db.get_collection('users').find_one({
        '_id': message.from_user.id
    })
    user_table = user['user_table']
    df: pd.DataFrame = parse_gtable(user_table)

    search = df.transpose().iloc[0].str.contains(student_substr, case=False)
    res_df = df[search]
    if res_df.empty:
        return SEARCH_NOT_FOUND_TEXT

    matched_students = df[search].transpose().iloc[0].values.tolist()
    return '\n'.join(matched_students)
