import sqlite3


def create_database(db_name='test'):
    conn = sqlite3.connect(f'{db_name}.db')
    c = conn.cursor()
    
    # User table
    c.execute('CREATE TABLE IF NOT EXISTS User(id integer primary key, name text, chat_id integer, '
              'notification_band integer DEFAULT 85, notification_day integer DEFAULT 25, notification_traffic integer DEFAULT 50,'
              ' date text)')
    
    # Virtualizor API details
    c.execute('CREATE TABLE IF NOT EXISTS API_DETAIL(id integer primary key, chat_id INTEGER,'
              'end_point text, api_key text UNIQUE, api_pass text UNIQUE, date text,'
              'FOREIGN KEY (chat_id) REFERENCES User (chat_id))')
    
    # SolusVM API details
    c.execute('CREATE TABLE IF NOT EXISTS SOLUSVM_API_DETAIL(id integer primary key, chat_id INTEGER,'
              'base_url text, api_key text, server_id text, date text,'
              'FOREIGN KEY (chat_id) REFERENCES User (chat_id))')
    
    # Virtualizor VS notifications
    c.execute('CREATE TABLE IF NOT EXISTS VS_NOTIFICATION(id integer primary key, vps_id integer unique, chat_id INTEGER,'
              'notification_band integer DEFAULT 0, notification_day integer DEFAULT 0,'
              'notification_traffic integer DEFAULT 0, date text,'
              'FOREIGN KEY (chat_id) REFERENCES User (chat_id))')
    
    # SolusVM VS notifications
    c.execute('CREATE TABLE IF NOT EXISTS SOLUSVM_VS_NOTIFICATION(id integer primary key, vps_id integer unique, chat_id INTEGER,'
              'notification_band integer DEFAULT 0, notification_day integer DEFAULT 0,'
              'notification_traffic integer DEFAULT 0, date text,'
              'FOREIGN KEY (chat_id) REFERENCES User (chat_id))')
    
    # Uncomment these if you need to add columns to existing tables
    # c.execute('ALTER TABLE VS_NOTIFICATION ADD COLUMN notification_traffic integer DEFAULT 0')
    # c.execute('ALTER TABLE User ADD COLUMN notification_traffic integer DEFAULT 50')
    
    conn.commit()
    conn.close()
