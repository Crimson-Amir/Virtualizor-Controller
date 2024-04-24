import sqlite3


def create_database(db_name='test'):
    conn = sqlite3.connect(f'{db_name}.db')
    c = conn.cursor()

    c.execute('CREATE TABLE IF NOT EXISTS User(id integer primary key, name text, chat_id integer, '
              'notification_band integer DEFAULT 85, notification_day integer DEFAULT 25, date text)')

    c.execute('CREATE TABLE IF NOT EXISTS API_DETAIL(id integer primary key, chat_id INTEGER,'
              'end_point text, api_key text UNIQUE, api_pass text UNIQUE, date text,'
              'FOREIGN KEY (chat_id) REFERENCES User (chat_id))')

    c.execute('CREATE TABLE IF NOT EXISTS VS_NOTIFICATION(id integer primary key, vps_id integer unique, chat_id INTEGER,'
              'notification_band integer, notification_day integer, date text,'
              'FOREIGN KEY (chat_id) REFERENCES User (chat_id))')

    conn.commit()
    conn.close()
