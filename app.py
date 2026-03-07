from flask import Flask, render_template
from threading import Thread
import webview
from flask_socketio import SocketIO
import multiprocessing as mp
from main import main

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

@app.route("/")
def home():
    return render_template("index.html")


def get_results():
    while True:
        result = result_queue.get()
        print(f'result from classifier: {result}')
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
        webview.create_window("Log-Spy", "http://127.0.0.1:5000")
        webview.start()
    finally:
        print("Window closed - signalling Main-process shut-down...")
        stop_event.set()    # signal main() to shut down gracefully
        
        main_process.join(timeout=8)

        if main_process.is_alive(): # Force shut-down
            print("Main-process force shut-down...")
            main_process.kill()
            main_process.join()

            print("All processes stopped.")