import psycopg2
import sys

def reset_database():
    db_url = "postgresql://postgres:urban@localhost:5432/infrapredict"
    print(f"Connecting to database to reset public schema...")
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        with conn.cursor() as cur:
            print("Dropping public schema...")
            cur.execute("DROP SCHEMA IF EXISTS public CASCADE;")
            print("Creating public schema...")
            cur.execute("CREATE SCHEMA public;")
            cur.execute("GRANT ALL ON SCHEMA public TO postgres;")
            cur.execute("GRANT ALL ON SCHEMA public TO public;")
        conn.close()
        print("Database schema successfully reset!")
    except Exception as e:
        print(f"Error resetting database: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    reset_database()
