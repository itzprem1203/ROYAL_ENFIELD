import psycopg2
import json

# Database connection details
DB_HOST = "192.168.8.25"  # Client's PC IP
DB_NAME = "Multi_Gauge"  # Database name
DB_USER = "postgres"  # Default PostgreSQL user
DB_PASSWORD = "sai@123"  # Given password
DB_PORT = "5432"  # Default PostgreSQL port

try:
    # Connect to the remote database
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    cur = conn.cursor()

    # Query to fetch data
    query = "SELECT * FROM probe_calibrations;"
    print('your query values in this from your table:',query)
    cur.execute(query)

    # Fetch all rows
    rows = cur.fetchall()

    # Print fetched data
    for row in rows:
        print(json.dumps(row, indent=4))

    # Close the connection
    cur.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
