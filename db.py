import psycopg2
import json

# ---- DB Connection Config ----
db_config = {
    'host': '98.80.57.76',
    'port': 5432,
    'database': 'htmlgen',
    'user': 'postgres',
    'password': 'Bajarang2o25@'
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
