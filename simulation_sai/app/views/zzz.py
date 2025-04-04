import os
import subprocess
import datetime

# Database configuration
db_name = "postgres"
db_user = "postgres"
db_password = "sai@123"
db_host = "localhost"
db_port = "5432"

# Path to pg_dump executable
pg_dump_path = r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe"

# Get the current user's Downloads folder path
downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")

# Create a timestamp for the backup file name
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# Name the backup file
backup_file = f"backup_{db_name}_{timestamp}.sql"

# Full path to store the backup in the Downloads folder
backup_file_path = os.path.join(downloads_path, backup_file)

# The pg_dump command
pg_dump_command = f'"{pg_dump_path}" -h {db_host} -U {db_user} -p {db_port} -F c -b -v -f "{backup_file_path}" {db_name}'

# Set the environment variable for password
os.environ['PGPASSWORD'] = db_password

try:
    # Run the pg_dump command
    subprocess.run(pg_dump_command, shell=True, check=True)
    print(f"Backup successful! File saved at: {backup_file_path}")
except subprocess.CalledProcessError as e:
    print(f"Error during backup: {str(e)}")
