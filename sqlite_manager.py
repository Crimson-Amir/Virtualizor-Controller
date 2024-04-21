import sqlite3
import functools
from utilities import report_problem_to_admin

class ManageDb:
    def __init__(self, db_name: str = "test"):
        self.db_name = db_name + ".db"

    @staticmethod
    def handle_exceptions(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                err = f"[{type(e)}] An error occurred in {func.__name__}:\n{str(e)}"
                report_problem_to_admin(err)
                return e

        return wrapper

    @staticmethod
    def init_name(name):
        if isinstance(name, str):
            return name.replace("'", "").replace('"', "")
        else:
            return name


    def create_table(self, table: dict):
        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            for key, val in table.items():
                coul = [f"{name} {v}" for name, v in val.items()]
                cursor.execute("CREATE TABLE IF NOT EXISTS {0} ({1})".format(key, ", ".join(coul)))
            db.commit()


    def select(self, column: str = "*", table: str = "sqlite_master",
               where: str = None, distinct: bool = False, order_by: str = None,
               limit: int = None):
        distinct_ = "DISTINCT " if distinct else ''
        order_by_ = f'ORDER BY {order_by}' if order_by else ''
        limit_ = f'LIMIT {limit}' if limit else ''
        where_ = f'WHERE {where}' if where else ''

        sql = f"SELECT {distinct_}{column} FROM {table} {where_} {order_by_} {limit_}"

        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            cursor.execute(sql)
            db_values = cursor.fetchall()
        return db_values


    @handle_exceptions
    def insert(self, table: str, rows: dict):
        column = ', '.join(rows.keys())
        values = [f"'{self.init_name(val)}'" for val in rows.values()]

        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            cursor.execute(f'INSERT INTO {table} ({column}) VALUES ({", ".join(values)})')
            db.commit()
        return cursor.lastrowid


    def delete(self, table: dict):
        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            for key, value in table.items():
                cursor.execute(f"DELETE FROM {key} WHERE {value[0]}='{value[1]}'")
            db.commit()


    def advanced_delete(self, table):
        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            for key, value in table.items():
                where = ''
                for arg in value:
                    key_ = arg[0]
                    val_ = arg[1] if type(arg[1]) is int else f'"{arg[1]}"'
                    where += f'{key_} = {val_} AND '
                cursor.execute(f"DELETE FROM {key} WHERE {where[:-4]}")
            db.commit()


    def drop_table(self, table: str):
        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            db.commit()


    def update(self, table, where):
        where = f'where {where}' or None

        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            for key, value in table.items():
                for k, v in value.items():
                    text = f"UPDATE {key} SET {k} = '{self.init_name(v)}' {where}"
                    cursor.execute(text)
                db.commit()
        return cursor.lastrowid


    def custom(self, order: str, return_fetcall=True):
        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            cursor.execute(order)
            db.commit()
        if return_fetcall:
            return cursor.fetchall()


    def custom_multi(self, *order):
        with sqlite3.connect(self.db_name) as db:
            cursor = db.cursor()
            for order_ in order:
                cursor.execute(order_)
                db.commit()

# t = {
#     "student": {
#         "id": "integer primary key",
#         "name": "TEXT",
#         "family": "TEXT",
#         "age": "INTEGER"
#     },
#     "teacher": {
#         "name": "TEXT",
#         "family": "TEXT",
#         "age": "INTEGER"
#     }
# }
# a = ManageDb()
# a.create_table(t)
# print(a.custom("SELECT name from sqlite_master where type='table'"))
# a.insert(table='student', rows=[{'name': 'amir', 'family': 'najafi', 'age': 21}, {'name': 'fsd', 'family': 'sfd', 'age': 34}])
# a.delete({'student': ['name', 'amir']})
# a.drop_table('teacher')
# print(a.order_by(table='student'))
# print(a.select(table='student'))