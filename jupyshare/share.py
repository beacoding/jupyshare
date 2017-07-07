import subprocess 
import re
import os
from clint.textui import colored
import requests
import webbrowser
import argparse
import time
import sys
import pickle
import shelve

def parser():
    parser = argparse.ArgumentParser(description='Share Your Jupyter Notebook in the Cloud')
    parser.add_argument('--browser', action='store', help='Either chrome, firefox, or safari', default='chrome')
    parser.add_argument('action', action='store', help='Either release / kill / show')

    args = parser.parse_args()
    return args

def get_notebooks(jshare_db):
    notebooks = {}

    if (sys.version_info > (3, 0)):
        stdoutdata = subprocess.getoutput("jupyter notebook list")
    else:
        stdoutdata = subprocess.check_output("jupyter notebook list", shell=True)

    x = stdoutdata.split("http://localhost:")[1:]

    for val in x:
        separated = val.split('::')
        location = separated[1].strip()
        port_token = separated[0].split("token=")
        port, token = re.sub(r'[?|$|.|!/\/]',r'',port_token[0]), port_token[1].strip()
        try:
            jshare_db[port]
            ngrok_processes, ngrok_dict = get_live_processes()

            if port not in ngrok_dict:
                del jshare_db[port]

            if location != jshare_db[port][0]:
                os.system('kill {}'.format(ngrok_dict[port]))
                del jshare_db[port]

            raise Exception

        except Exception as e:
            notebooks[port] = [location, token]

    return notebooks

def get_live_notebooks(jshare_db):
    if len(jshare_db.keys()) == 0:
        print(colored.green('You have no live notebooks right now'))
        sys.exit(0)
    print(colored.green('\nThese are your live notebooks right now:'))
    ngrok_processes, ngrok_dict = get_live_processes()
    notebooks = get_notebooks(jshare_db)

    for key in jshare_db:
        if key in ngrok_dict:
            location = jshare_db[key][0]
            url = jshare_db[key][1]
            if key not in notebooks:
                os.system('kill {}'.format(ngrok_dict[key]))
                del jshare_db[key]
            else:
                print('     {} {}'.format(colored.cyan('| {} |'.format(key)), location))
                print('              {}'.format(colored.magenta(url)))


def get_live_processes():
    if (sys.version_info > (3, 0)):
        ngrok_processes = list(filter(lambda s: s.find("ngrok http") > -1, subprocess.getoutput("ps -o pid -o args").split("\n")))
    else:
        ngrok_processes = list(filter(lambda s: s.find("ngrok http") > -1, subprocess.check_output("ps -o pid -o args", shell=True).split("\n")))

    ngrok_dict = dict(list(map(lambda x: tuple(reversed(x.split(" ngrok http "))), ngrok_processes)))

    return ngrok_processes, ngrok_dict

def kill(jshare_db):
    ngrok_processes, ngrok_dict = get_live_processes()

    if len(ngrok_processes) == 0:
        print(colored.green('NO NOTEBOOKS ARE IN THE CLOUD'))
        sys.exit(0)
    
    print(colored.green("\nWhich tunnel do you want to kill? Type 'all' if you want to shut everything down"))
    
    for i, key in enumerate(ngrok_dict):
        if is_in_db(jshare_db, key):
            print('     {} {}'.format(colored.cyan('| {} |'.format(key)), jshare_db[key][0]))
        else:
            jshare_db[key] = ["Location unknown", "Url unknown"]
            print('     {} {}'.format(colored.cyan('| {} |'.format(key)), jshare_db[key][0]))
            

    while(1):
        if (sys.version_info > (3, 0)):
            port_chosen = input(colored.cyan('NOTEBOOK PORT: '))
        else:
            port_chosen = raw_input(colored.cyan('NOTEBOOK PORT: '))

        if port_chosen == 'q' or port_chosen == 'quit' or port_chosen == ':q':
            sys.exit(0)
        if port_chosen == 'all':
            for key in ngrok_dict:
                os.system('kill {}'.format(ngrok_dict[key]))
                print(colored.green("Killed notebook listening on port {}".format(key)))
            jshare_db.clear()
            sys.exit(0)
        if port_chosen in ngrok_dict:
            break
        else:
            print(colored.red('ERROR: MUST ENTER A VALID NOTEBOOK PORT'))
            continue

    os.system('kill {}'.format(ngrok_dict[port_chosen]))
    del jshare_db[port_chosen]
    print(colored.green("Killed notebook listening on port {}".format(port_chosen)))
    sys.exit(0)

def is_in_db(jshare_db, port):
    try:
        jshare_db[port]
        return True
    except Exception as e:
        return False

def release(jshare_db, args):
    print(colored.magenta("Grabbing open notebooks..."))
    time.sleep(2)

    raw_notebooks = get_notebooks(jshare_db)
    notebooks = {}

    for port in raw_notebooks:
        if not is_in_db(jshare_db, port):
            notebooks[port] = raw_notebooks[port]

    if len(notebooks) == 0:
        print(colored.green('NO NOTEBOOKS OPEN'))
        sys.exit(0)

    print(colored.green('\nWhich notebook are you referring to?'))

    for i, key in enumerate(notebooks):
        try:
            jshare_db[key]

        except Exception as e:
            print('     {} {}'.format(colored.cyan('| {} |'.format(key)), notebooks[key][0]))

    while(1):
        if (sys.version_info > (3, 0)):
            port_chosen = input(colored.cyan('NOTEBOOK PORT: '))
        else:
            port_chosen = raw_input(colored.cyan('NOTEBOOK PORT: '))
        if port_chosen == 'q' or port_chosen == 'quit' or port_chosen == ':q':
            sys.exit(0)
        if port_chosen in notebooks:
            break
        else:
            print(colored.red('ERROR: MUST ENTER A VALID NOTEBOOK PORT'))
            continue

    os.system('ngrok http {} > ngrok.log &'.format(port_chosen))

    print(colored.magenta("Opening notebook on port {} up...".format(port_chosen)))
    time.sleep(10)

    r = requests.get('http://127.0.0.1:4040/api/tunnels')
    r.raise_for_status()
    ngrok_url = r.json()['tunnels'][0]['public_url']

    notebook_url = ngrok_url + '/' + '?token=' + notebooks[port_chosen][1]

    jshare_db[port_chosen] = [notebooks[port_chosen][0], notebook_url]

    print(colored.green("Opened! To see a list of open notebooks try running jupyshare show"))
    print(colored.green("Your notebook is found on {}".format(notebook_url)))

    webbrowser.get(args.browser).open_new_tab(notebook_url)

def main():
    args = parser()
    curdir = os.path.dirname(__file__)
    jshare_db = shelve.open(os.path.join(curdir, 'jshare'))

    if args.action == 'kill':
        kill(jshare_db)
    elif args.action == 'release':
        release(jshare_db, args)
    elif args.action == 'show':
        get_live_notebooks(jshare_db)
    else:
        print(colored.red("Action must either be 'release' or 'kill' or 'show'"))
        print(colored.green("Try jupyshare release"))

    jshare_db.close()


if __name__ == '__main__':
    main()
