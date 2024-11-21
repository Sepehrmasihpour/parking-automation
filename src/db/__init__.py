import sqlite3

conn = sqlite3.connect("parking.db")
c = conn.cursor()

# Create the parking_tokens table
c.execute(
    """
    CREATE TABLE IF NOT EXISTS parking_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        is_paid BOOLEAN NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
)

# Create the GATE_STATUS table
c.execute(
    """
    CREATE TABLE IF NOT EXISTS GATE (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        open BOOLEAN NOT NULL DEFAULT 0
    )
    """
)


c.execute("INSERT OR IGNORE INTO GATE (name, open) VALUES ('entry', 0)")
c.execute("INSERT OR IGNORE INTO GATE (name, open) VALUES ('exit', 0)")

conn.commit()
conn.close()
