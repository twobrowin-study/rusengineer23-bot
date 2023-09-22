import sqlite3, hashlib

from tenacity import retry, wait_exponential, stop_after_attempt
from typing import Callable

HASH_TABLE  = 'hash_table'
KEY_COL     = 'key'
VAL_COL     = 'val'

class HashDbAbstract():
    def __init__(self, conn: str) -> None:
        self._conn: str  = conn
        self._connection: sqlite3.Connection = None
    
    def connected(self) -> bool:
        if self._connection is None:
            return False
        try:
            self._connection.execute(f"SELECT * FROM {HASH_TABLE} LIMIT 1;")
            return True
        except Exception:
            return False
    
    def connect(self):
        self.close()
        self._connection = sqlite3.connect(self._conn)

    def close(self):
        if self.connected():
            try:
                self._connection.close()
            except Exception:
                pass
        self._connection = None

    def reconnect(f: Callable):
        def wrapper(storage: HashDbAbstract, *args, **kwargs):
            if not storage.connected():
                storage.connect()
            try:
                return f(storage, *args, **kwargs)
            except Exception:
                storage.close()
                raise
        return wrapper

class HashDb(HashDbAbstract):
    @retry(stop=stop_after_attempt(3), wait=wait_exponential())
    @HashDbAbstract.reconnect
    def initialize_table(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute((
            f"CREATE TABLE IF NOT EXISTS {HASH_TABLE} ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                f"{KEY_COL} TEXT,"
                f"{VAL_COL} TEXT"
            ");"
        ))
        self._connection.commit()
        cursor.close()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential())
    @HashDbAbstract.reconnect
    def get_val(self, key: str) -> str | None:
        cursor = self._connection.cursor()
        cursor.execute(
            f"SELECT {VAL_COL} FROM {HASH_TABLE} "
            f"WHERE  {KEY_COL} = '{key}' "
            f"LIMIT 1;"
        )
        res = cursor.fetchone()
        cursor.close()
        if res is None:
            return None
        return res[0]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential())
    @HashDbAbstract.reconnect
    def add_val(self, val: str) -> str:
        cursor = self._connection.cursor()
        key = hashlib.sha256(val.encode()).hexdigest()
        cursor.execute((
            f"INSERT INTO {HASH_TABLE} "
            f"({KEY_COL}, {VAL_COL}) "
            f"VALUES ('{key}', '{val}');"
        ))
        self._connection.commit()
        cursor.close()
        return key
