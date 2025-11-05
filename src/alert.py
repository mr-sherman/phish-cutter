import emoji
from windows_toasts import Toast, WindowsToaster

def show_toast(text_fields):
    toaster = WindowsToaster("PhishCutter Alert")
    newToast = Toast()
    newToast.text_fields = text_fields
    toaster.show_toast(newToast)

def get_flag_text(score_breakdown:dict[str, float]):
    flags = ""
    if score_breakdown["company_domain_score"] > 0.0:
        flags = flags + " Company name mismatch "
    if score_breakdown["trusted_domain_score"] > 0.0:
        flags = flags  + " Trusted domain mismatch "
    if score_breakdown["phishy_words_score"] > 0.0:
        flags = flags + " Urgency language " 

    return flags

def alert(subject:str, sender:str, score_breakdown:dict[str, float]):
    flags = get_flag_text(score_breakdown)
    
    show_toast([f"{emoji.emojize(":police_car_light:")}: Phishing detected",f"sender: {sender}",f"subject: {subject}",f"Reasons: {flags}"] )
    print(f"{emoji.emojize(":police_car_light:")}: Phishing detected.\n   Sender: {sender}\n  Subject:{subject}\n  Reasons{flags}\n")

def warn(subject:str, sender:str, score_breakdown:dict[str, float]):
    flags = get_flag_text(score_breakdown)
    
    show_toast([f"{emoji.emojize(":warning:")}: Potential Phishing detected",f"sender: {sender}",f"subject: {subject}", f"Reasons: {flags}"])
    print(f"{emoji.emojize(":warning:")}: Potential Phishing detected.\n   Sender: {sender}\n  Subject:{subject}\n  Reasons{flags}\n")



