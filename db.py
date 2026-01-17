import psycopg2
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---- DB Connection Config ----
# Load database credentials from environment variables
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

# Validate that all required environment variables are set
required_vars = {
    'DB_HOST': db_host,
    'DB_PORT': db_port,
    'DB_NAME': db_name,
    'DB_USER': db_user,
    'DB_PASSWORD': db_password
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}. Please set them in .env file.")

db_config = {
    'host': db_host,
    'port': int(db_port),
    'database': db_name,
    'user': db_user,
    'password': db_password
}

# ---- Function to Fetch Data ----
def fetch_facebook_settings(record_id):
    try:
        # Connect to DB
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Query
        query = """
        SELECT page_id, page_access_token
        FROM facebook_settings
        WHERE id = %s;
        """
        cursor.execute(query, (record_id,))
        result = cursor.fetchone()

        if result:
            data = {
                'page_id': result[0],
                'page_access_token': result[1]
            }

            # Write to JSON file
            with open('facebook_settings.json', 'w') as f:
                json.dump(data, f, indent=4)

            print("Data saved to facebook_settings.json")

        else:
            print("No record found with that ID.")

        cursor.close()
        conn.close()

    except Exception as e:
        print("Error:", e)

# ---- Call the function with the ID you want to fetch ----
fetch_facebook_settings(2)  # Change 1 to the actual ID
