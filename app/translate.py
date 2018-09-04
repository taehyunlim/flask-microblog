import json
import requests
from flask_babel import _
from app import application

def translate(text, source_lang, dest_lang):
    if 'MS_TRANSLATOR_KEY' not in application.config or not application.config['MS_TRANSLATOR_KEY']:
        return _('Error: the translation service is not configured.')
    # Headers attribute for requests method
    auth = {'Ocp-Apim-Subscription-Key': application.config['MS_TRANSLATOR_KEY']}
    # requests.get
    r = requests.get('https://api.microsofttranslator.com/v2/Ajax.svc/Translate?text={}&from={}&to={}'.format(text, source_lang, dest_lang), headers=auth)
    if r.status_code != 200:
        return _('Error: the translation service failed.')
    return json.loads(r.content.decode('utf-8-sig'))
