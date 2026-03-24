from dotenv import load_dotenv
from groq import Groq
import os
import json
from datetime import datetime

load_dotenv()


def get_target_comps(user_input, timeframe_str):
    with open("troubleshooter/intent_sys_prompt.txt", 'r', encoding='utf-8') as f:
        sys_prompt = f.read()
    
    now = datetime.now()
    current_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    user_prompt = f"""Current timestamp: {current_timestamp}

User problem description:
"{user_input}"

Timeframe: last {timeframe_str}"""

    # Groq client initialization
    key = os.getenv("GROQ_API_KEY_1")
    groq = Groq(api_key=key)

    try:
        chat_completion = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": sys_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            model="llama-3.3-70b-versatile",
        )

        content = chat_completion.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Exception in component identifier: {e}")
        raise


def format_logs_for_prompt(collected):
    sections = []

    for component, data in collected.items():
        if component == "_fallback":
            header = "FALLBACK SOURCE (syslog/dmesg)"
        else:
            header = f"COMPONENT: {component} (unit: {data['unit']}, confidence: {data['confidence']})"

        # Timeframe context
        if data["fetch_method"] == "no_logs_found":
            timeframe_note = "  [NO LOGS FOUND — do not speculate about this component]"
        elif data["timeframe_expanded"]:
            timeframe_note = f"  [NOTE: logs expanded to {data['timeframe_used']} — wider than user-specified timeframe]"
        else:
            timeframe_note = f"  [Timeframe: {data['timeframe_used']}]"

        # Log lines
        if data["logs"]:
            log_block = "\n".join(f"  {line}" for line in data["logs"])
        else:
            log_block = "  (no log entries)"

        sections.append(f"{header}\n{timeframe_note}\n{log_block}")

    return "\n\n".join(sections)


def find_root_cause(log_data, intent):
    formatted_logs = format_logs_for_prompt(log_data)
    
    with open("troubleshooter/rc_sys_prompt.txt", 'r', encoding='utf-8') as f:
        sys_prompt = f.read()

        user_prompt = f"""Problem description: "{intent['problem_summary']}"
User-specified timeframe: {intent['timeframe']['value']}

Collected logs by component:
{formatted_logs}"""

    # Groq client initialization
    key = os.getenv("GROQ_API_KEY_2")
    groq = Groq(api_key=key)

    try:
        chat_completion = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": sys_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            model="openai/gpt-oss-120b",
            reasoning_effort="medium"
        )

        content = chat_completion.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Exception in component identifier: {e}")
        raise



if __name__ == "__main__":
    from log_fetcher import fetch_logs
    #user_statement = "My wifi is being disconnected repeatedly and somtimes getting deauthenticated."
    user_statement = "I cannot mount or access the drive named 'Windows'. It shows failed to mount that drive."
    timeframe = "1h"
    targets = get_target_comps(user_statement, timeframe)
    collected_logs = fetch_logs(targets)
    print(find_root_cause(collected_logs, targets))
