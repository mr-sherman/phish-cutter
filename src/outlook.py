import win32com.client
import pythoncom

DEFAULT_FOLDER = 6


# COM event sink bound to the Outlook Application. Outlook fires OnNewMailEx
# for each item delivered to the inbox, passing a comma-separated list of
# EntryIDs which we resolve back to mail items via the MAPI namespace.
class _NewMailHandler:
    def OnNewMailEx(self, entry_id_collection):
        callback = getattr(self, "callback", None)
        namespace = getattr(self, "namespace", None)
        if callback is None or namespace is None:
            return
        for entry_id in entry_id_collection.split(","):
            try:
                item = namespace.GetItemFromID(entry_id)
            except Exception:
                # Non-mail items (meeting requests, etc.) may not resolve.
                continue
            callback(item)


class outlook:

    # Constructor - open the outlook inbox
    def __init__(self):
        try:
    # Try to get the already running instance of Outlook
            app = win32com.client.GetActiveObject("Outlook.Application")
        except Exception as e:
    # If not running, create a new instance
            try:
                app = win32com.client.Dispatch("Outlook.Application")
            except Exception as e:
                print(f"Error: Could not connect or start Outlook. {e}")
                raise e
        self.app = app
        self.outlook = app.GetNamespace("MAPI")
        self.inbox = self.outlook.GetDefaultFolder(DEFAULT_FOLDER)

    # return all emails since the timestamp (used for startup catch-up)
    def get_emails(self, timestamp):
        filter_string = f"[ReceivedTime] >= '{timestamp}'"

        filtered_emails = self.inbox.Items.Restrict(filter_string)

        return filtered_emails

    # register a callback to be invoked for each newly arrived email
    def watch(self, callback):
        handler = win32com.client.WithEvents(self.app, _NewMailHandler)
        handler.callback = callback
        handler.namespace = self.outlook
        # keep a reference so the event sink isn't garbage collected
        self._handler = handler

    # process any pending Outlook events; call repeatedly from a loop
    def pump(self):
        pythoncom.PumpWaitingMessages()
