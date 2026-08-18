import os
import pg8000.dbapi
from urllib.parse import urlparse, unquote

# Read from environment or load from .env
CRDB_URL = os.environ.get("CRDB_URL")
if not CRDB_URL and os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("CRDB_URL="):
                CRDB_URL = line.split("=", 1)[1].strip().strip('"').strip("'")

def get_connection():
    if not CRDB_URL:
        raise ValueError("CRDB_URL environment variable is not set and not found in .env")
    p = urlparse(CRDB_URL)
    params = {
        "host": p.hostname,
        "port": p.port or 26257,
        "user": unquote(p.username or ""),
        "password": unquote(p.password or ""),
        "database": (p.path or "/defaultdb").lstrip("/"),
        "ssl_context": __import__("ssl").create_default_context(),
        "timeout": 15,
    }
    return pg8000.dbapi.connect(**params)

def run_sql():
    print("Connecting to CockroachDB...")
    
    try:
        conn = get_connection()
        conn.autocommit = True
        cur = conn.cursor()
        print("Enabling vector index cluster setting...")
        cur.execute("SET CLUSTER SETTING feature.vector_index.enabled = true;")
        print("  Vector index cluster setting enabled successfully.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"  Note: Cluster setting check/enable failed (often because it's already enabled or user lacks permissions): {e}")

    conn = get_connection()
    cur = conn.cursor()

    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schema.sql")
    print(f"Reading schema from {schema_path}...")
    with open(schema_path, "r") as f:
        sql_commands = f.read()

    commands = [cmd.strip() for cmd in sql_commands.split(";") if cmd.strip()]
    for cmd in commands:
        first_line = cmd.split('\n')[0]
        print(f"Executing: {first_line} ...")
        try:
            cur.execute(cmd)
            conn.commit()
            print("  Success")
        except Exception as e:
            print(f"  Error executing command: {e}")
            conn.rollback()
            raise e

    print("Verifying tables...")
    cur.execute("SHOW TABLES;")
    tables = cur.fetchall()
    print("Tables present:")
    for t in tables:
        print(f"  - {t[0]}")

    cur.close()
    conn.close()
    print("Database initialization complete!")

if __name__ == "__main__":
    run_sql()
