
class phish_cutter_config:
    def __init__(self, config):
        self.config = config
        self.defaults = {
            "phish_test_headers": [
                "x-threatsim-id",
                "x-phishtest",
                "x-phishme",
                "x-phish-crid"
            ]
        }
    def __getitem__(self, key):
        try:
            ret_val = self.config[key]
        except KeyError as k:
            ret_val = self.defaults[key]
        finally:
            return ret_val