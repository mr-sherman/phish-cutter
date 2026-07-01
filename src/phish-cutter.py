from difflib import SequenceMatcher as sm
import pyfiglet
from datetime import datetime
from outlook import outlook
import time
import phish_analyzer as pa
import alert
import os
import json
import logging
from logging.handlers import RotatingFileHandler
import yaml

PHISH_ANALYZER = None

PHISH_CUTTER = "Phish Cutter"

LAST_RUN_FILE = "./.last-run"

LOG_FILE = "./phish-cutter.log"
logger = logging.getLogger("phish_cutter")

CONFIG_FILE = "config/config.yaml"

# Placeholder company domains shipped in the sample/default config; if the
# config still holds one of these we prompt the user for their real domain.
PLACEHOLDER_DOMAINS = {"company.com", "mycompany.com", "my-company.com"}

# Persisted guard against re-processing the same email (e.g. the boundary
# email straddling a restart, which startup catch-up would otherwise re-scan).
SEEN_FILE = "./.seen"
MAX_SEEN = 1000
SEEN_IDS = set()
SEEN_ORDER = []

CONFIG = None

def setup_logging():
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        # rotate so the log file stays bounded (5 x 1MB)
        handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=5)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)

def write_timestamp(filename):
    with open(filename, "w") as f:
        f.write(datetime.now().strftime('%m/%d/%Y %I:%M %p'))

def read_timestamp(filename):
    with open(filename, "r") as f:
        timestamp = f.read()
    return timestamp

def load_seen():
    global SEEN_IDS, SEEN_ORDER
    try:
        with open(SEEN_FILE, "r") as f:
            SEEN_ORDER = json.load(f)
    except (FileNotFoundError, ValueError):
        SEEN_ORDER = []
    # keep only the most recent MAX_SEEN in case an older file is larger
    SEEN_ORDER = SEEN_ORDER[-MAX_SEEN:]
    SEEN_IDS = set(SEEN_ORDER)

def save_seen():
    with open(SEEN_FILE, "w") as f:
        json.dump(SEEN_ORDER, f)

def mark_seen(entry_id):
    if entry_id in SEEN_IDS:
        return
    SEEN_IDS.add(entry_id)
    SEEN_ORDER.append(entry_id)
    # bound the history so the file doesn't grow without limit
    while len(SEEN_ORDER) > MAX_SEEN:
        SEEN_IDS.discard(SEEN_ORDER.pop(0))
    save_seen()

def create_config():
    default_config = {
        "thresholds": 
        {
            "alert": .35,
            "warn": .25
        },
        "phish_test_headers": [
               "x-threatsim-id",
                "x-phishtest",
                "x-phishme",
                "x-phish-crid"
            ],
        "company_domain": "my-company.com",
        "trusted_domains": [
            "sharepoint.com",
            "office.com",
            "m365.cloud.microsoft",
            "github.com",
            "percipio.com",
            "myworkday.com",
            "yammer.com"
        ],
        "phishy_words":[
            "urgent",
            "important",
            "now",
            "limited",
            "hurry",
            "required",
            "action",
            "click here",
            "go here"
        ],
        "poll_interval":10
    }
    if not os.path.exists("./config"):
        os.mkdir("./config")
    with open("config/config.yaml", "w") as f:
        f.write(yaml.dump(default_config))
    
        

def _replace_company_domain(domain):
    # rewrite only the company_domain line so config comments are preserved
    with open(CONFIG_FILE, "r") as f:
        lines = f.readlines()
    replaced = False
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("company_domain:") and not stripped.startswith("#"):
            indent = line[:len(line) - len(stripped)]
            lines[i] = f"{indent}company_domain: {domain}\n"
            replaced = True
            break
    if not replaced:
        lines.append(f"company_domain: {domain}\n")
    with open(CONFIG_FILE, "w") as f:
        f.writelines(lines)

# If the config still has a placeholder company domain, ask the user for their
# real one and save it so we never have to ask again.
def ensure_company_domain():
    with open(CONFIG_FILE, "r") as f:
        config = yaml.safe_load(f)
    current = str(config.get("company_domain", "")).strip().lower()
    if current not in PLACEHOLDER_DOMAINS:
        return
    print("Your company email domain has not been configured yet.")
    while True:
        entry = input("Enter your work email address (or company domain): ").strip()
        if not entry:
            print("No domain entered; leaving configuration unchanged.")
            logger.info("company_domain left unconfigured (no input)")
            return
        domain = entry.split("@")[-1].strip().lower()
        if "." in domain:
            break
        print("That doesn't look like a valid domain. Please try again.")
    _replace_company_domain(domain)
    logger.info("Set company_domain to %s", domain)
    print(f"Saved company domain '{domain}' to {CONFIG_FILE}")

def process_email(e):
    try:
        entry_id = e.EntryID
    except Exception:
        entry_id = None
    if entry_id is not None and entry_id in SEEN_IDS:
        return
    try:
        sender = e.SenderEmailAddress
        subject = e.Subject
        try:
            attachment_count = e.Attachments.Count
        except Exception:
            attachment_count = 0
        logger.info(
            "Email received - sender: %s, subject: %s, has_attachments: %s (%d)",
            sender, subject, attachment_count > 0, attachment_count)

        if e.SenderEmailType == "EX":
            logger.info("Skipping internal (Exchange) sender: %s", sender)
            return
        prop_accessor = e.PropertyAccessor
        header = prop_accessor.GetProperty("http://schemas.microsoft.com/mapi/proptag/0x007D001E")

        score_breakdown = PHISH_ANALYZER.analyze(sender, subject, e.Body, header)
        score = score_breakdown["company_domain_score"] + score_breakdown["trusted_domain_score"] + score_breakdown["phishy_words_score"]
        logger.info(
            "Analyzed - sender: %s, subject: %s, phish_test_header: %s, total_score: %.3f, "
            "breakdown{company_domain: %.3f, trusted_domain: %.3f, phishy_words: %.3f, phish_test: %.3f}",
            sender, subject, score_breakdown["phish_test_score"] > 0.0, score,
            score_breakdown["company_domain_score"], score_breakdown["trusted_domain_score"],
            score_breakdown["phishy_words_score"], score_breakdown["phish_test_score"])
        if score > PHISH_ANALYZER.get_config()["thresholds"]["alert"]:
            logger.warning("ALERT (phishing) - sender: %s, subject: %s, score: %.3f", sender, subject, score)
            alert.alert(subject=e.Subject, sender=e.SenderEmailAddress, score_breakdown=score_breakdown)
        elif score > PHISH_ANALYZER.get_config()["thresholds"]["warn"]:
            logger.warning("WARN (potential phishing) - sender: %s, subject: %s, score: %.3f", sender, subject, score)
            alert.warn(subject=e.Subject, sender=e.SenderEmailAddress, score_breakdown=score_breakdown)
    except Exception as ex:
        logger.exception("Error processing email")
    finally:
        if entry_id is not None:
            mark_seen(entry_id)
        write_timestamp(LAST_RUN_FILE)


# Process any mail that arrived while Phish Cutter was not running, so we
# don't miss emails between the last run and now.
def catch_up(mailbox):
    try:
        timestamp = read_timestamp(LAST_RUN_FILE)
    except FileNotFoundError as e:
        return
    for e in mailbox.get_emails(timestamp):
        process_email(e)
    write_timestamp(LAST_RUN_FILE)


def watch_email(mailbox):
    load_seen()
    logger.info("Catching up on mail received while stopped")
    catch_up(mailbox)
    mailbox.watch(process_email)
    logger.info("Watching inbox for new mail")
    try:
        while True:
            mailbox.pump()
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        logger.exception("Error while watching inbox")
    finally:
        write_timestamp(LAST_RUN_FILE)
        logger.info("Phish Cutter stopped")
        print("Closing")

if __name__ == "__main__":
    setup_logging()
    logger.info("Phish Cutter starting")
    art_gen = pyfiglet.Figlet(font="doom")
    title = art_gen.renderText(PHISH_CUTTER)
    if not os.path.exists("config/config.yaml"):
        create_config()
    ensure_company_domain()
    PHISH_ANALYZER = pa.phish_analyzer("config/config.yaml")
    try:
        mailbox = outlook()

        print(title)
        print("Watching inbox. Control-C to stop")

        watch_email(mailbox)
    except Exception as e:
        logger.exception("Could not open Outlook")
        print("Cannot open outlook email.\nClose all your outlook windows and shut down outlook from the system tray as well.\nThen re-run Phish Cutter")
    print("exiting")
