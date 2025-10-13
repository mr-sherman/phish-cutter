import emoji
from windows_toasts import Toast, WindowsToaster

def show_toast(text_fields):
    toaster = WindowsToaster("PhishCutter Alert")
    newToast = Toast()
    newToast.text_fields = text_fields
    toaster.show_toast(newToast)

def alert(subject:str, sender:str):
    show_toast([f"{emoji.emojize(":police_car_light:")}: Phishing detected",f"sender: {sender}",f"subject: {subject}"])
    
def warn(subject:str, sender:str):
    show_toast([f"{emoji.emojize(":warning:")}: Potential Phishing detected",f"sender: {sender}",f"subject: {subject}"])
    


