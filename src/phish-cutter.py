from difflib import SequenceMatcher as sm
import pyfiglet
from datetime import datetime
from outlook import outlook
import time
import phish_analyzer as pa
import alert

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

def poll_email(mailbox):
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
                prop_accessor = e.PropertyAccessor
                header = prop_accessor.GetProperty("http://schemas.microsoft.com/mapi/proptag/0x007D001E")
                
                score_breakdown = PHISH_ANALYZER.analyze(e.SenderEmailAddress, e.Subject, e.Body, header)
                score = score_breakdown["company_domain_score"] + score_breakdown["trusted_domain_score"] + score_breakdown["phishy_words_score"]
                if score > PHISH_ANALYZER.get_config()["thresholds"]["alert"]:
                    alert.alert(subject=e.Subject, sender=e.SenderEmailAddress, score_breakdown=score_breakdown)
                elif score > PHISH_ANALYZER.get_config()["thresholds"]["warn"]:
                    alert.warn(subject=e.Subject, sender=e.SenderEmailAddress, score_breakdown=score_breakdown) 
            write_timestamp(LAST_RUN_FILE)
            time.sleep(PHISH_ANALYZER.get_config()["poll_interval"])

    except KeyboardInterrupt:
        pass
    except Exception as ex:
        pass
    finally:
        write_timestamp(LAST_RUN_FILE)
        print("Closing")

if __name__ == "__main__":
    art_gen = pyfiglet.Figlet(font="doom")
    title = art_gen.renderText(PHISH_CUTTER)

    PHISH_ANALYZER = pa.phish_analyzer("config/config.yaml")
    try:
        mailbox = outlook()

        print(title)
        print("Control-C to stop")

        poll_email(mailbox)
    except Exception as e:
        print("Cannot open outlook email.\nClose all your outlook windows and shut down outlook from the system tray as well.\nThen re-run Phish Cutter")
    print("exiting")
