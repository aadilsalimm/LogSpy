from flask import Flask
import threading
from flask_socketio import SocketIO
import multiprocessing as mp
from main import main

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')

@app.route("/")
def home():
    return "LogSpy running..."


def get_results():
    while True:
        result = result_queue.get()
        # print(f'result from classifier: {result}')
        socketio.emit("anomaly_update", result)


if __name__ == "__main__":
    result_queue = mp.Queue()
    main_process = mp.Process(target=main, args=(result_queue,))
    main_process.start()
    
    threading.Thread(target=get_results, daemon=True).start()

    try:
        # app.run(debug=True, use_reloader=False)
        socketio.run(app, debug=False, use_reloader=False)
    finally:
        main_process.terminate()
        main_process.join()