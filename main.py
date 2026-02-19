import multiprocessing as mp
import json
from datetime import datetime, timezone, timedelta
from log_shipper import LogShipper
from log_classifierV1 import LogClassifier

def main(result_to_app):
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

    # Controller loop
    while True:
        logs = logs_from_shipper.get()
        logs_to_classifier.put(logs)
        result = result_from_classifier.get()
        # print(f'result: {result}')

        json_result = json.loads(result)

        # Modifying the timestamp from Unix epoch to human-readable form
        ts = json_result["timestamp"]
        ist = timezone(timedelta(hours=5, minutes=30))
        dt = datetime.fromtimestamp(ts / 1_000_000, tz=ist)
        json_result["timestamp"] = dt.strftime("%Y-%m-%d %H:%M:%S")
        # print(dt.strftime("%Y-%m-%d %H:%M:%S"))


        result_to_app.put(json_result)
        # is_anomalous = json_result.get("is_anomalous")
        # print(f'returned value: {is_anomalous}')
        # print(f'result: {json_result}')

        

    
if __name__ == "__main__":
    dummy_queue = mp.Queue()
    main(dummy_queue)