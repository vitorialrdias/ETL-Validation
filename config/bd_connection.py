from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from config.logging import logger
import urllib

class Database:
    def __init__(self, host, database, user, password, port=3306):
        self.engine = None
        
        engine_params = {
            "pool_size": 20, 
            "max_overflow": 12, 
            "pool_timeout": 30.0, 
            "fast_executemany": True, 
            "pool_pre_ping": True
        }

        try:
            if '186' in host:
                params = urllib.parse.quote_plus(
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={host};DATABASE={database};"
                    f"UID={user};PWD={password}"
                )
                url = f"mssql+pyodbc:///?odbc_connect={params}"
            else:
                url = f'mssql+pyodbc://{user}:{password}@{host}/{database}?driver=ODBC+Driver+17+for+SQL+Server'
            
            self.engine = create_engine(url, **engine_params)
        except SQLAlchemyError as e:
            logger.error(f"Error to create engine: {e}")
            raise

    def get_connection(self):
        """Return active connection."""
        return self.engine.connect()

    def dispose(self):
        """Close connection."""
        if self.engine:
            self.engine.dispose()