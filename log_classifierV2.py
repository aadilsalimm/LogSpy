import subprocess
import re
import json
import requests
import time
import socket


# TODO: Write about model set-up on Ollama in the readme file.
class LogClassifier:
    def __init__(self):

        def is_ollama_running():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('127.0.0.1', 11434)) == 0
        
        if not is_ollama_running():
            print("Initializing Ollama...")
            subprocess.Popen(["ollama", "serve"])
            time.sleep(5)
        else:
            print("Ollama already running")


    def ollama_call(self, log_msgs):

        def extract_fields(response_txt):
            patterns = {
                "is_anomalous": r'"is_anomalous"\s*:\s*([01])',
                "timestamp":    r'"timestamp"\s*:\s*"([^"]*)"',
                "reason":       r'"reason"\s*:\s*"([^"]*)"',
            }

            results = {}
            for key, pattern in patterns.items():
                match = re.search(pattern, response_txt)
                if match:
                    results[key] = match.group(1)
                else:
                    results[key] = "null"

            return results
        

        try:
            prompt = f'''The given log messages are from linux journalctl.
            Analyze them and find if there is any anomalous behaviour or not.
            Give output strictly in the following JSON format:
            {{"is_anomalous":<0/1>,"timestamp":<timestamp>,"reason":<concise description of reason in one or two lines>}}
            Remember: THE OUTPUT MUST STRICTLY IN THE ABOVE FORMAT WITH NO OTHER CHARACTERS.
            Log messages: {log_msgs}'''

            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "finetuned_phi_3.5:latest",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                },
                stream=True
            )

            response.raise_for_status()  # will raise clearly on 404/500 etc.

            full_response = ""
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    full_response += data["message"]["content"]

            # print(f'llm output: {full_response}')

            return json.dumps(extract_fields(full_response))
            
        except Exception as e:
            print(f'Exception in classifier: {e}')


    def classify(self, input_queue, output_queue):
        while True:
            log_msgs = input_queue.get()
            result = self.ollama_call(log_msgs)
            output_queue.put(result)




if __name__ == "__main__":
    classifier = LogClassifier()
    
    log_msg = json.dumps([{"systemd_unit":"null","syslog_identifier":"sudo","priority":1,"message":"pam_unix(sudo:auth): authentication failure; logname= uid=1000 euid=0 tty=/dev/pts/0 ruser=user rhost=  user=user","timestamp":1771838167627141},{"systemd_unit":"null","syslog_identifier":"nginx","priority":3,"message":"worker process 33387 exited on signal 11","timestamp":1771838172806673},{"systemd_unit":"user@1000.service","syslog_identifier":"nginx","priority":3,"message":"worker process 24122 exited on signal 11","timestamp":1771838172956082},{"systemd_unit":"null","syslog_identifier":"sshd","priority":3,"message":"Failed password for invalid user admin from 83.185.43.149 port 16833 ssh2","timestamp":1771838178287067},{"systemd_unit":"null","syslog_identifier":"kernel","priority":3,"message":"Out of memory: Killed process 33444 (java) total-vm:456789kB, anon-rss:12345kB, file-rss:0kB","timestamp":1771838183512459}])
    result = classifier.ollama_call(log_msg)
    print(f'result: {result}')