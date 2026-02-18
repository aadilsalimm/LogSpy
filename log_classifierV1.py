from dotenv import load_dotenv
from groq import Groq
import json
import re


class LogClassifier:
    def __init__(self):
        load_dotenv()
        self.groq = Groq()

    # TODO : Add timestamp
    def groq_api_call(self, log_msgs):
        try:
            prompt = f'''The given log messages are from linux journalctl.
            Analyze them and find if there is any anomalous behaviour or not.
            Give a one-word output strictly in the following JSON format:
            {{"logs":<log sequence -> add all logs in the sequence>, "is_anomalous":<0/1>, "reason":<<concise description of reason in one or two lines>}}
            Remember: THE OUTPUT MUST STRICTLY IN THE ABOVE JSON FORMAT.
            Log messages: {log_msgs}'''

            chat_completion = self.groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.1
            )

            content = chat_completion.choices[0].message.content
            return content
        except Exception as e:
            print(f"Exception in classifier: {e}")


    def classify(self, input_queue, output_queue):
        while True:
            log_msgs = input_queue.get()
            result = self.groq_api_call(log_msgs)
            output_queue.put(result)