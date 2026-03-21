import multiprocessing as mp
import json
from datetime import datetime, timezone, timedelta
from .log_shipper import LogShipper
from .log_classifier import LogClassifier

def main(result_to_app, stop_event):
    logs_from_shipper = mp.Queue()
    logs_to_classifier = mp.Queue()
    result_from_classifier = mp.Queue()

    shipper = LogShipper(buffer_size=5, filter_logs=True)
    classifier = LogClassifier()

    shipper_process = mp.Process(
        target=shipper.start,
        args=(logs_from_shipper,)
    )

    classifier_process = mp.Process(
        target=classifier.classify,
        args=(logs_to_classifier,
              result_from_classifier,)
    )

    shipper_process.start()
    classifier_process.start()

    try:
        # Controller loop
        while not stop_event.is_set():
            try:
                logs = logs_from_shipper.get(timeout=1)
            except mp.queues.Empty:
                continue

            logs_to_classifier.put(logs)

            try:
                result = result_from_classifier.get()        
            except mp.queues.Empty:
                print("Classifier timed out, skipping batch")
                continue

            json_result = json.loads(result)

            # Modifying the timestamp from Unix epoch to human-readable IST
            ts = json_result["timestamp"]
            try:
                if ts and ts != "null":
                    ist = timezone(timedelta(hours=5, minutes=30))
                    dt = datetime.fromtimestamp(ts / 1_000_000, tz=ist)
                    json_result["timestamp"] = dt.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    json_result["timestamp"] = "unknown"
            except Exception as e:
                print(f"Timestamp parse error: {e}")
                json_result["timestamp"] = "unknown"


            result_to_app.put(json_result)

    finally:
        print("Shutting down shipper and classifier...")
        shipper_process.terminate()
        classifier_process.terminate()
        shipper_process.join(timeout=3)
        classifier_process.join(timeout=3)

        if shipper_process.is_alive():
            shipper_process.kill()
        if classifier_process.is_alive():
            classifier_process.kill()
        
        print("Main process shut down complete.")


        

    
if __name__ == "__main__":
    dummy_queue = mp.Queue()
    main(dummy_queue)