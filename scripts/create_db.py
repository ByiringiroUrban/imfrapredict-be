import sys
import os
from sqlalchemy import create_engine, text

# Add parent directory to sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings

def create_db():
    settings = get_settings()
    db_url = settings.sync_database_url
    base_url, db_name = db_url.rsplit('/', 1)
    
    query_params = ""
    if "?" in db_name:
        db_name, query_params = db_name.split("?", 1)
        query_params = "?" + query_params
    
    postgres_url = f"{base_url}/postgres{query_params}"
    
    print(f"Connecting to default database to check/create '{db_name}'...")
    engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'"))
            exists = result.scalar()
            
            if not exists:
                print(f"Database '{db_name}' does not exist. Creating...")
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"Database '{db_name}' created successfully!")
            else:
                print(f"Database '{db_name}' already exists.")
    except Exception as e:
        print(f"Error checking/creating database: {e}", file=sys.stderr)
        print("Please check if your PostgreSQL service is running and credentials in backend/.env are correct.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    create_db()
