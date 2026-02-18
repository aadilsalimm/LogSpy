from flask import Flask
import multiprocessing
from main import main

app = Flask(__name__)

@app.route("/")
def home():
    return "LogSpy running..."


if __name__ == "__main__":
    main_process = multiprocessing.Process(target=main)
    main_process.start()
    
    try:
        app.run(debug=True, use_reloader=False)
    finally:
        main_process.terminate()
        main_process.join()