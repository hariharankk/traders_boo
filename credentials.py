from sys import exit
import yaml
import argparse
import os


def load_config(file):
    try:
       if os.path.isfile(file):
          with open(file) as file:
              return yaml.load(file)
    except FileNotFoundError as fe:
        exit(f'Could not find {file}')
    
    except Exception as e:
        exit(f'Encountered exception...\n {e}')

def load_correct_creds():
    try:
        creds = load_config('creds.yml')
        return creds['prod']['host'], creds['prod']['pass'], int(creds['prod']['port'])
    
    except TypeError as te:
        message = 'Your credentials are formatted incorectly\n'
        message += f'TypeError:Exception:\n\t{str(te)}'
        exit(message)
    except Exception as e:
        message = 'oopsies, looks like you did something real bad. Fallback Exception caught...\n'
        message += f'Exception:\n\t{str(e)}'
        exit(message)


