from flask import Flask, render_template
from threading import Thread, Timer
import webbrowser
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


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")


if __name__ == "__main__":
    result_queue = mp.Queue()
    main_process = mp.Process(target=main, args=(result_queue,))
    main_process.start()
    
    Thread(target=get_results, daemon=True).start()

    try:
        Timer(1, open_browser).start()
        socketio.run(app, debug=False, use_reloader=False)
    finally:
        main_process.terminate()
        main_process.join()