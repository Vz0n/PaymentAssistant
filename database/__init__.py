from sqlite3 import connect, Cursor
from os import environ

class Database:
    def __init__(self):
        self.name = environ["DB_FILENAME"]
        self.handle = connect(self.name)

    # Executes modify/update operations
    def execute_query(self, stmt, *params) -> list[tuple[any]] | tuple[any]:
        cursor = self.handle.cursor()
        data = cursor.execute(stmt, params).fetchall()

        cursor.close()

        if len(data) == 1:
            return data[0]
        
        return data

    # Executes fetch/query operations
    def execute_update(self, stmt, *params) -> None:
        cursor = self.handle.cursor()    
        cursor.execute(stmt, params)
        cursor.close()

        # Commit changes to the database file
        self.handle.commit()

    # Get a raw sqlite cursor for *really* big operations.
    def get_raw_cursor(self) -> Cursor:
        return self.handle.cursor()
    
    # Commit queued changes.
    def commit_changes(self):
        self.handle.commit()
    
    def run_update_statements(self, statements: list[str]):
        for stmt in statements:
            self.execute_update(stmt)

    def close(self):
        return self.handle.close()