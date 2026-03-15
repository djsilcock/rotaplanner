from strawberry.fastapi import BaseContext

import sqlite3


class CustomContext(BaseContext):
    def __init__(self, connection: sqlite3.Connection):
        from .dataloaders import DataLoaders  # Import here to avoid circular import

        self.connection = connection
        self.data_loaders = DataLoaders(connection)
