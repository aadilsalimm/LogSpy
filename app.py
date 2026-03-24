from flask import Flask, render_template
from threading import Thread
import webview
from flask_socketio import SocketIO
import multiprocessing as mp
from log_spy.main import main
import log_spy.db_ops as db
import troubleshooter.troubleShooter as ts
from troubleshooter.log_fetcher import fetch_logs

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")
db.connect_db()

@app.route("/")
def home():
    return render_template("log_spy.html")

@app.route("/troubleshooter")
def troubleshooter():
    return render_template("troubleshooter.html")


# Log-Spy Event Handlers
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


# Troubleshooter Event Handlers
@socketio.on("troubleshoot")
def handle_troubleshoot(data):
    user_input = data.get("problem", "None")
    timeframe = data.get("timeframe", "1h")

    try:
        # Step 1: Identify components
        socketio.emit("troubleshoot_step", {"step": 1})
        target_components = ts.get_target_comps(user_input=user_input, timeframe_str=timeframe)

        # Step 2: Fetch logs
        socketio.emit("troubleshoot_step", {"step": 2})
        collected_logs = fetch_logs(target_components)

        # Step 3: Analyze root cause
        socketio.emit("troubleshoot_step", {"step": 3})
        result = ts.find_root_cause(collected_logs, target_components)

        # Sending result to front-end
        socketio.emit("troubleshoot_result", result)
        
    except Exception as e:
        socketio.emit("troubleshoot_error", {"message": str(e)})


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