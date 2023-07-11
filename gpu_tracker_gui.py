import PySimpleGUI as sg
import smtplib
import requests
from bs4 import BeautifulSoup
import traceback
import datetime
from msrp_finder import get_msrp
import csv
import os.path
import getpass

URL = 'https://www.newegg.com/p/pl?d='

def interval_in_s(string):
    unit = string[len(string)-1]
    t = int(string[0:-1])
    match unit:
        case 'm':
            t*=60
        case 'h':
            t*=3600
        case 'd':
            t*=3600*24
    return t

def validate_title(terms, string, include_resell):
    resell_check = True if include_resell else validate_resell(string)
    string = string.split()
    inString = 0
    for term in terms:
        for s in string:
            if term.lower() in s.lower():
                inString += 1
    return inString >= len(terms) and resell_check

def validate_resell(string):
    terms = ['resell', 'refurbished', 'old', 'open', 'used']
    words = string.split()
    for word in words:
        if word.lower() in terms:
            return False
    return True

params = {
    'query':'RTX 3080', 
    'price_trigger':699,
    'send_to':'johnsencorey@gmail.com'
}

# Go to https://myaccount.google.com/apppasswords to make an app password for Python
# and then use that generated password to log in

with open('email_config.txt') as f:
    sender_email = f.readline().strip()
    sender_password = f.readlines()[0].strip()

layout=[]
title_column = []
field_column = []
for param in params:
    title = param.replace('_', ' ').capitalize()
    title_column.append([sg.Text(f'{title}:')])
    char_type = '•' if param=='sender_password' else ''
    field_column.append([sg.InputText(params[param], key=param, password_char=char_type)])

title_column.append([sg.Text('Time interval:')])
field_column.append([sg.InputText('5s', key='interval')])
title_column.append([sg.Text('Iterations:')])
field_column.append([sg.InputText('5', key='iterations')])
title_column.append([sg.Text('Include resells?')])
field_column.append([sg.Checkbox('', key='resells')])

layout.append([
    sg.Column(title_column),
    sg.Column(field_column)
])

layout.append([sg.Button('Monitor'), sg.Button('Quit'), sg.Button('Cancel Monitoring', disabled=True, key='Cancel Monitoring')])
layout.append([sg.Text('Output:')])
layout.append([sg.Output(key='output', size=(60,10))])

window = sg.Window(
    'GPU Price Tracker', 
    layout
)

counter = 0

server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(sender_email, sender_password)

isMonitoring = False

while True:
    event, values = window.read(timeout=500)
    if isMonitoring and counter >= params['time_interval']:
        counter = 0
        try:
            page = requests.get(params['full_query'],headers={"User-Agent":"Defined"})
            soup = BeautifulSoup(page.content, 'html.parser')
            cells = soup.find_all(class_='item-cell')

            for i in range(3):
                for cell in cells:
                    if cell.find(class_='item-title') == None or cell.find(class_='price-current').text == None:
                        cells.remove(cell)

                for cell in cells:
                    if not validate_title(params['query'].split(' '), cell.find(class_='item-title').text, params['include_resell']):
                        cells.remove(cell)

            prices = {}
            for cell in cells:
                price_txt = cell.find(class_='price-current').text
                try:
                    price = float(price_txt.split()[0].replace('$', '').replace(',', '') if ' ' in price_txt else price_txt.replace('$', '').replace(',', ''))
                except:
                    # TODO: fix this
                    price = float('inf')
                prices[price] = cell.find(class_='item-title').text
            price_keys = list(prices.keys())
            price_keys.sort()

            with open(f'price_hist/{ params["query"].replace(" ", "_").lower()}.csv', 'a') as f:
                    fields=['date','price']
                    writer = csv.DictWriter(f, fields, delimiter=',', lineterminator='\n')
                    for p in price_keys:
                        writer.writerow({'date':datetime.datetime.utcnow(), 'price':int(p)}) if p != float('inf') else None

            filtered_prices = list(filter(lambda p: p <= params['price_trigger'], price_keys))

            if len(filtered_prices) > 0:
                search = params['query']
                trigger = params['price_trigger']
                message = f'Subject: Automated trigger for {search}\n\n(Automated alert for {search})\nThe following products have dropped to ${trigger}:\n'
                for p in filtered_prices:
                    message += f' - {prices[p]} (${p})\n'

                server.sendmail(from_addr=sender_email, to_addrs=params['send_to'], msg=message.encode('ascii', 'ignore').decode('ascii'))
                print(f'{datetime.datetime.utcnow()}: Message sent for {len(filtered_prices)} products triggered')

            else:
                print(f'{datetime.datetime.utcnow()}: Price checked, no results')
        except Exception as e:
            print(traceback.format_exc())
    counter += .5
    if event == sg.WIN_CLOSED or event == 'Quit': # if user closes window or clicks cancel
        break
    elif event == 'Cancel Monitoring':
        isMonitoring = False
        window['Monitor'].update(disabled=False)
        window['Cancel Monitoring'].update(disabled=True)
        print('----Monitoring Cancelled----')
    elif event == 'Monitor':
        window['output'].update(disabled=True)
        window['Monitor'].update(disabled=True)

        # update input_params
        try:
            isMonitoring = True
            params['query'] = values['query']
            params['price_trigger'] = get_msrp(params['query']) if values['price_trigger'].lower() == 'msrp' else float(values['price_trigger'])
            params['send_to'] = values['send_to']
            params['time_interval'] = interval_in_s(values['interval'])
            params['iterations'] = int(values['iterations'])
            params['url'] = URL
            params['sender_email'] = sender_email
            params['sender_password'] = sender_password
            params['full_query'] = params['url'] + params['query'].replace(' ', '+')
            params['include_resell'] = values['resells']
            window['Cancel Monitoring'].update(disabled=False)
            print('----Monitoring Started----')
            counter = params['time_interval']
            file_exists = os.path.isfile(f'price_hist/{ params["query"].replace(" ", "_").lower()}.csv')
            with open(f'price_hist/{ params["query"].replace(" ", "_").lower()}.csv', 'a') as f:
                fields=['date','price']
                writer = csv.DictWriter(f, fields, delimiter=',', lineterminator='\n')

                if not file_exists:
                    writer.writeheader()
        except ValueError:
            print('GPU not found. Check inputs and try again. (MSRP input only works with GPUs)')
            window['Monitor'].update(disabled=False)
            window['Cancel Monitoring'].update(disabled=True)
            isMonitoring = False
        except:
            print('Invalid parameters! Please check your inputs and try again.')
            window['Monitor'].update(disabled=False)
            window['Cancel Monitoring'].update(disabled=True)
            isMonitoring = False

window.close()