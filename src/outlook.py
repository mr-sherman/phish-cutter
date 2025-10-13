import win32com.client
from datetime import datetime, timedelta

DEFAULT_FOLDER = 6

class outlook:

    # Constructor - open the outlook inbox
    def __init__(self):
        self.outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        self.inbox = self.outlook.GetDefaultFolder(DEFAULT_FOLDER)

    # return all emails since the timestamp
    def get_emails(self, timestamp):
        filter_string = f"[ReceivedTime] >= '{timestamp}'"

        filtered_emails = self.inbox.Items.Restrict(filter_string)

        return filtered_emails
