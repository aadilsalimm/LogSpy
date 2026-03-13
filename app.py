from flask import Flask, render_template
from threading import Thread
import webview
from flask_socketio import SocketIO
import multiprocessing as mp
from main import main
import db_ops as db

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")
db.connect_db()

@app.route("/")
def home():
    return render_template("index.html")


# Socket.IO Event Handlers
@socketio.on("get_full_history")
def full_history_handler():
    history = db.get_all_data()
    socketio.emit("full_history", history)


@socketio.on("delete_logs")
def delete_logs_handler(ids):
    if not ids or not isinstance(ids, list):
        return
    db.delete_data(ids)
    

@socketio.on("clear_history")
def clear_history_handler():
    db.clear_data()


def get_results():
    while True:
        result = result_queue.get()
        print(f'result from classifier: {result}')
        db.add_data(result)
        socketio.emit("anomaly_update", result)


def run_server():
    socketio.run(app, debug=False, use_reloader=False)


if __name__ == "__main__":
    result_queue = mp.Queue()
    stop_event = mp.Event()
    main_process = mp.Process(target=main, args=(result_queue, stop_event))
    main_process.start()
    
    Thread(target=get_results, daemon=True).start()

    try:
        Thread(target=run_server, daemon=True).start()
        webview.create_window(title="Log-Spy", url="http://127.0.0.1:5000", width=1200, height=800)
        webview.start()
    finally:
        print("Window closed - signalling Main-process shut-down...")
        db.close_db_connection()
        stop_event.set()    # signal main() to shut down gracefully
        
        main_process.join(timeout=8)

        if main_process.is_alive(): # Force shut-down
            print("Main-process force shut-down...")
            main_process.kill()
            main_process.join()

            print("All processes stopped.")