import subprocess
import sys
from log_filter import preprocess_logs, should_filter

class LogShipper:
    def __init__(self, buffer_size=10, filter_logs=True):
        self.buffer_size = buffer_size
        self.buffer = []
        self.process = None
        self.filter_logs = filter_logs

    def start(self, log_queue):
        """Starts the journalctl subprocess."""
        self.log_queue = log_queue
        try:
            self.process = subprocess.Popen(
                ['journalctl', '-f', '-o', 'json', '-n', '0'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, # Decode bytes to string
                bufsize=1  # Line buffered
            )
            print(f"Log shipper started with buffer size {self.buffer_size}")
            self.capture_loop()
        except FileNotFoundError:
            print("Error: journalctl command not found from log_shipper.py in start method.")
            sys.exit(1)
        except Exception as e:
            print(f"Error starting log shipper: {e}")
            sys.exit(1)

    def capture_loop(self):
        """Continuously reads from the subprocess stdout."""
        if not self.process:
            return

        try:
            while True:
                # Read a line from stdout
                line = self.process.stdout.readline()
                if not line:
                    # Process ended or stream closed
                    break
                
                self.add_to_buffer(line.strip())
                
        except KeyboardInterrupt:
            print("\nStopping log shipper...")
            self.flush_buffer() # Flush remaining logs before exit
            self.process.terminate()
        except Exception as e:
            print(f"Error in capture loop: {e}")
        # finally:
        #     if self.process:
        #         self.process.kill()

    def add_to_buffer(self, log_entry):
        """Adds a log entry to the buffer and checks if flush is needed."""
        if not log_entry:
            return

        # Skip unwanted log messages
        if self.filter_logs and should_filter(log_entry):
            return
        
        # Filter unwanted fields from the log message
        filtered_log = preprocess_logs(log_entry)
        self.buffer.append(str(filtered_log))

        self.buffer.append(log_entry)
        
        if len(self.buffer) >= self.buffer_size:
            self.flush_buffer()

    def flush_buffer(self):
        """Outputs the buffered logs and clears the buffer."""
        if not self.buffer:
            return

        print(f"Flushing {len(self.buffer)} logs...")
        logs = ""
        for log in self.buffer:
            logs = logs + '\n' + log
        self.buffer.clear()
        self.log_queue.put(logs)

if __name__ == "__main__":
    # Default buffer size is 10, can be changed here or via args if expanded
    shipper = LogShipper(buffer_size=10)
    shipper.start()
