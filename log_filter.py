import json
import re

def preprocess_logs(input_log):
    try:
        log_entry = json.loads(input_log.strip())

        cleaned_entry = {
            "systemd_unit": log_entry.get("_SYSTEMD_UNIT"),
            "syslog_identifier": log_entry.get("SYSLOG_IDENTIFIER"),
            "priority": int(log_entry["PRIORITY"]) if "PRIORITY" in log_entry else None,
            "message": log_entry.get("MESSAGE"),
            "timestamp": int(log_entry["__REALTIME_TIMESTAMP"]) if "__REALTIME_TIMESTAMP" in log_entry else None,
            # "pid": int(log_entry["_PID"]) if "_PID" in log_entry else None,
            # "hostname": log_entry.get("_HOSTNAME"),
        }

        # Skip empty or invalid messages
        if cleaned_entry["message"]:
            return cleaned_entry

    except json.JSONDecodeError as e:
        print(f"Json decode error: {e}")
        pass  # skip malformed lines




def should_filter(input_log, drop_info_level=True):
    """
    Returns True if log should be filtered out.
    Returns False if log should be kept.
    """

    log_entry = json.loads(input_log.strip())

    BLACKLIST_IDENTIFIERS = {
    "gnome-shell",
    "xkbcomp",
    "avahi-daemon",
    "pipewire",
    "wireplumber",
    "cups",
    "cups-browsed",
    "snapd",
    "tracker",
    "tracker-miner-fs",
    "brave-browser.desktop",
}


    MESSAGE_PATTERNS = [
        r"CTRL-EVENT-SIGNAL-CHANGE",      # WiFi signal spam
        r"Overwriting existing binding",  # GNOME key warnings
        r"Could not resolve keysym",      # XKB warnings
        r"CompositorAnimationObserver",   # Browser compositor spam
        r"Successfully activated",        # dbus routine activation
        r"Starting .*\.service",          # systemd routine start
        r"Started .*\.service",
        r"Deactivated successfully",
        r"Lockdown: systemd-logind: hibernation is restricted;",
    ]

    COMPILED_PATTERNS = [re.compile(p) for p in MESSAGE_PATTERNS]


    identifier = log_entry.get("SYSLOG_IDENTIFIER", "")
    message = log_entry.get("MESSAGE", "")
    priority = log_entry.get("PRIORITY")

    if identifier in BLACKLIST_IDENTIFIERS: # Identifier blacklist
        return True

    if identifier == "wpa_supplicant" and "CTRL-EVENT-SIGNAL-CHANGE" in message:    # WiFi signal spam
        return True

    if identifier == "NetworkManager" and "<info>" in message:  # Routine NetworkManager info logs
        return True

    if identifier == "systemd": # systemd routine lifecycle noise
        if any(pattern.search(message) for pattern in COMPILED_PATTERNS):
            return True

    for pattern in COMPILED_PATTERNS:   # Message pattern filtering
        if pattern.search(message):
            return True

    if drop_info_level: # Drop informational logs
        try:
            if priority is not None and int(priority) >= 6:
                return True
        except ValueError:
            pass

    return False




if __name__ == "__main__":
    log_msg = '''{"_SELINUX_CONTEXT":"unconfined\\n","SYSLOG_IDENTIFIER":"wpa_supplicant","PRIORITY":"5","__REALTIME_TIMESTAMP":"1771152541827242","_HOSTNAME":"aadil-Victus","MESSAGE":"wlp4s0: CTRL-EVENT-SIGNAL-CHANGE above=1 signal=-48 noise=9999 txrate=270000","_PID":"949","_SYSTEMD_UNIT":"wpa_supplicant.service"}'''
    
    #print(preprocess_logs(log_msg))
    print(f"Should be filtered?: {should_filter(log_msg)}")