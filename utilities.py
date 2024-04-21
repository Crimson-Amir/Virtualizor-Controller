import requests
from private import telegram_bot_url, ADMIN_CHAT_ID
import functools
import arrow
from datetime import datetime

def report_problem_to_admin(msg):
    requests.post(telegram_bot_url, data={'chat_id': ADMIN_CHAT_ID, 'text': msg})


def handle_error(func):
    @functools.wraps(func)
    def warpper(update, context):
        user_detail = update.effective_chat
        try:
            return func(update, context)
        except Exception as e:
            err = f"🔴 [{type(e)}] An error occurred in {func.__name__}:\n{str(e)}\nuser chat id: {user_detail.id}"
            print(err)
            report_problem_to_admin(err)
            context.bot.send_message(text='Sorry! somthing went wrong!', chat_id=user_detail.id)
    return warpper


def replace_with_space(txt):
    return txt.replace('_', ' ')

def human_readable(number):
    get_date = arrow.get(number)
    return get_date.humanize()


def unix_time_to_datetime(date):
    return datetime.fromtimestamp(date)
