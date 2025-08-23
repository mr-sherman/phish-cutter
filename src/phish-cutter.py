from difflib import SequenceMatcher as sm
import yaml
import pyfiglet
from datetime import datetime
from outlook import outlook
import time
import phish_analyzer as pa

PHISH_ANALYZER = None

PHISH_CUTTER = "Phish Cutter"

LAST_RUN_FILE = "./.last-run"

CONFIG = None

def write_timestamp(filename):
    with open(filename, "w") as f:
        f.write(datetime.now().strftime('%m/%d/%Y %I:%M %p'))

def read_timestamp(filename):
    with open(filename, "r") as f:
        timestamp = f.read()
    return timestamp

def load_config(path):
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def poll_email(mailbox, interval):
    try:
        while True:
            try:
                timestamp = read_timestamp(LAST_RUN_FILE)
            except FileNotFoundError as e:
                timestamp = datetime.now().strftime('%m/%d/%Y %I:%M %p')
            emails = mailbox.get_emails(timestamp)

            for e in emails:
                if e.SenderEmailType == "EX":
                    continue
                score = PHISH_ANALYZER.analyze(e.SenderEmailAddress, e.Subject, e.Body)
                if score > CONFIG["thresholds"]["alert"]:
                    print(f"ALERT! Phishing email detected from {e.SenderEmailAddress}, subject = {e.Subject}\n")
                elif score > CONFIG["thresholds"]["warn"]:
                    print (f"Warning!  Potential - this looks phishy from {e.SenderEmailAddress}, Subject = {e.Subject}")

            write_timestamp(LAST_RUN_FILE)
            time.sleep(interval)

    except KeyboardInterrupt:
        pass
    finally:
        write_timestamp(LAST_RUN_FILE)
        print("Closing")

if __name__ == "__main__":
    art_gen = pyfiglet.Figlet(font="doom")
    title = art_gen.renderText(PHISH_CUTTER)

    CONFIG = load_config("config/config.yaml")
    PHISH_ANALYZER = pa.phish_analyzer(CONFIG)
    try:
        mailbox = outlook()

        print(title)
        print("Control-C to stop")

        poll_interval = CONFIG["poll_interval"]
        poll_email(mailbox, poll_interval*60)
    except:
        print("Cannot open outlook email.\nClose all your outlook windows and shut down outlook from the system tray as well.\nThen re-run Phish Cutter")
    print("exiting")
