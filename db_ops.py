import sqlite3

db_connection = None

def connect_db():
    global db_connection
    db_connection = sqlite3.connect('history.db', check_same_thread=False)
    db_connection.row_factory = sqlite3.Row

def add_data(data):
    cur = db_connection.cursor()
    query = f'''INSERT INTO history (timestamp, is_anomalous, component, description)
                VALUES(
                '{data['timestamp']}',
                {data['is_anomalous']},
                '{data['component']}',
                '{data['reason']}')'''
    cur.execute(query)
    db_connection.commit()


def clear_data():
    cur = db_connection.cursor()
    cur.execute('DELETE FROM history')
    db_connection.commit()


def delete_data(id):
    cur = db_connection.cursor()
    cur.execute(f'''DELETE FROM history WHERE id = {id} ''')
    db_connection.commit()


def get_all_data():
    cur = db_connection.cursor()
    cur.execute('SELECT * FROM history')
    rows = cur.fetchall()

    return [
        {
            "id": int(row["id"]),
            "timestamp": row["timestamp"],
            "is_anomalous": bool(row["is_anomalous"]),
            "component": row["component"],
            "reason": row["description"]
        }
        for row in rows
    ]
    


def close_db_connection():
    db_connection.close()




if __name__ == "__main__":
    import json
    raw_data = '''{"is_anomalous": 0, "timestamp": "2026-03-13 19:15:27", "reason": "The logs show normal user authentication and authorization activities, including sudo commands and lockdown restrictions.", "component": "Authentication/Authorization"}'''
    data = json.loads(raw_data)
    connect_db()
    add_data(data)
    # # clear_data()
    # connect_db()
    # delete_data("2026-03-13 19:15:27")
    # connect_db()
    print(get_all_data())
    close_db_connection()