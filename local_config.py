import logging
LOG_LEVEL = 30 # To be deprecated when all microservices use ADSFlask
LOGGING_LEVEL = "INFO"
LOG_STDOUT = True
EXPORT_SERVICE_CLASSIC_EXPORT_URL = ""
EXPORT_SOLRQUERY_URL = ""
EXPORT_SERVICE_ADSWS_API_TOKEN = ''
EXPORT_SERVICE_FROM_BBB_URL = ""

# added by eb-deploy (over-write config values) from environment
try:
    import os, json, ast
    G = globals()
    for k, v in os.environ.items():
        if k == k.upper() and k in G:
            logging.info("Overwriting constant '%s' old value '%s' with new value '%s'", k, G[k], v)
            try:
                w = json.loads(v)
                G[k] = w
            except:
                try:
                    # Interpret numbers, booleans, etc...
                    G[k] = ast.literal_eval(v)
                except:
                    # String
                    G[k] = v
except:
    pass
