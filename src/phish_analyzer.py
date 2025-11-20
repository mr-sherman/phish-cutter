from difflib import SequenceMatcher as sm
from config import phish_cutter_config
import yaml

class phish_analyzer:
    def __load_config(self):
        with open(self.config_filepath, 'r') as f:
            self.config = phish_cutter_config(yaml.safe_load(f))

        self.trusted_domains = self.config["trusted_domains"]
        self.company_domain = self.config["company_domain"]
        self.phishy_words = self.config["phishy_words"]
        self.alert = float(self.config["thresholds"]["alert"])
        self.warn = float(self.config["thresholds"]["warn"])
        self.phish_test_headers = self.config["phish_test_headers"]

    def __init__(self, filepath):
        self.config_filepath = filepath
        self.__load_config()
    
    def __get_email__domain(self, email_address):
        try:
            full_domain = email_address.split("@")[1]
            dot_count = full_domain.count(".")
            if dot_count == 1:
                return full_domain
            else:
                dot_index = full_domain.find(".")
                full_domain = full_domain[dot_index+1:]
                return full_domain
        except IndexError as i:
            pass
        return ""
    
    def get_config(self):
        return self.config
    
    def analyze(self, from_address, subject, body, header):
        self.__load_config()
        
        domain = self.__get_email__domain(from_address)
        
        company_domain_score = 0.0
        phishy_words_score = 0.0
        trusted_domain_score = 0.0
        phish_test_score = 0.0

        #check for phish test headers
        for h in self.phish_test_headers:
            if header.lower().find(h) > -1:
                phish_test_score = 1.0
                break

        company = self.company_domain[0:self.company_domain.find(".")]
        sender_domain = domain[0:domain.find(".")]
        company_domain_score = sm(None, company.upper(), sender_domain.upper() ).ratio()
        
        # if the company domain and the domain of the sender 
        # are exactly the same then it's not phishing
        if company_domain_score == 1.0:
            return {"company_domain_score": 0.0, 
                "trusted_domain_score": 0.0, 
                "phishy_words_score": 0.0,
                "phish_test_score":0.0} 
        
        max_ratio = 0.0
        for w in self.trusted_domains:
            trusted_domain = w[0:w.find(".")]
            ratio = sm(None, trusted_domain.upper(), sender_domain.upper()).ratio()
            if ratio == 1.0:
                trusted_domain_score = 0.0
                return {"company_domain_score": 0.0, 
                "trusted_domain_score": 0.0, 
                "phishy_words_score": 0.0,
                "phish_test_score":0.0} 
            if ratio > 0.4 and ratio < 1.0:
                if ratio > max_ratio:
                    max_ratio = ratio
        
        trusted_domain_score = max_ratio
            
        for w in self.phishy_words:
            if w.upper() in body.upper() or w.upper() in subject.upper():
                phishy_words_score += 0.25

        final_score = company_domain_score  + trusted_domain_score + phishy_words_score
        return {
                "phish_test_score": phish_test_score,
                "company_domain_score": company_domain_score, 
                "trusted_domain_score": trusted_domain_score, 
                "phishy_words_score": phishy_words_score}
