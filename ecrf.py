import argparse
import requests
from bs4 import BeautifulSoup
import re, time


def main():
    parser = argparse.ArgumentParser(description='Control ECRF v2 with Python!!')
    parser.add_argument('-f', '--frequency', type=float, required=False, help='frequency in MHz')
    parser.add_argument('-d', '--deviation', type=float, default=0, help='deviation in kHz [default: 0]')
    parser.add_argument('-mod', '--module', type=int, default=1, help='module number [module 1, module 2]')
    parser.add_argument('-m', '--modulation', type=int, default=2, help='modulation type [1: 2FSK, 2: ASK]')
    parser.add_argument('-t', '--transmissions', type=int, default=1, help='number of transmissions [default: 1]')
    parser.add_argument('-rxbw', '--rxbw', type=int, default=650, help='set rxbw [default: 650]')
    parser.add_argument('-dr', '--datarate', type=int, default=5, help='datarate [default: 5]')
    parser.add_argument('-rx', '--rxconfig', help='configure rx mode', action='store_true')
    parser.add_argument('-tx', '--txconfig', help='configure tx mode', action='store_true')
    parser.add_argument('-tesla', '--tesla', help='sends tesla charging port signal', action='store_true')
    parser.add_argument('--delete', help='delete logs/cleanspiffs', action='store_true')
    parser.add_argument('-o', '--output', help='specify output file for captured logs', type=str)
    parser.add_argument('-txoutput', '--txoutput', help='specify previously saved files to transmit', required=False, type=str)

    args = parser.parse_args()

    frequency = args.frequency
    deviation = args.deviation
    mod = args.module
    modulation = args.modulation
    transmissions = args.transmissions
    rxbw = args.rxbw
    datarate = args.datarate
    rxconfig = args.rxconfig
    txconfig = args.txconfig
    tesla = args.tesla
    delete = args.delete
    txoutput = args.txoutput

    # send tesla signals
    if tesla:
        print("[*] Opening charging port..")
        teslaTx(transmissions)

    if delete:
        print('[*] Deleting logs and cleaning spiffs')
        deleteClean()

    if args.output != None:
        print(f'[*] Saving logs to {args.output}')
        payloads = formatCapture()
        # if frequency etc. is not specified when -o is passed, ask for input
        if frequency == None:
            frequency = float(input(f'[*] Enter the frequency the logs are operating on: '))
            modulation = input(f'[*] Enter the modulation the logs are operating on [FSK/ASK]: ')
            if 'FSK' in modulation or 'fsk' in modulation:
                modulation = 1
                deviation = int(input(f'[*] Enter the deviation the logs are operating on: '))

        with open(args.output, 'w') as file:
            file.write(f'Frequency: {frequency}')
            file.write(f'Modulation: {modulation}')
            file.write(f'Deviation: {deviation}')
            for payload in payloads:
                file.write(f'Payload: {payload}')

    # if output file, send payloads in file
    if txoutput != None:
        print(f"[*] Transmitting from {txoutput}")
        with open(txoutput, 'r') as file:
            for line in file:
                if 'Frequency:' in line:
                    frequency = line.split(':')[1].strip()
                elif 'Modulation:' in line:
                    modulation = line.split(':')[1].strip()
                    if 'fsk' in modulation or 'FSK' in modulation:
                        modulation = 1
                    else:
                        modulation = 2
                elif 'Deviation:' in line:
                    deviation = line.split(':')[1].strip()
                elif 'Payload:' in line:
                    payloads = line.split(':')[1:]
                    payloads = [payload.strip() for payload in payloads]
        print(f"Frequency: {frequency}\nModulation: {modulation}\nDeviation: {deviation}")
        print("[*] Sending payloads.. ")
        txConfig(mod, modulation, frequency, deviation, transmissions, payloads)

    if txconfig:
        # grab logs
        payloads = formatCapture()
        txConfig(mod, modulation, frequency, deviation, transmissions, payloads)
    elif rxconfig:
        rxConfig(mod, modulation, frequency, rxbw, deviation, datarate)

# configure rx
def rxConfig(mod, modulation, frequency, rxbw, deviation, datarate):
    url = 'http://192.168.4.1/setrx'
    payload = {
        'module': f'{mod}', # be sure to use module 2 (ie -mod 2) for receiving 2FSK signals.
        'mod': f'{modulation}', # 1: FSK, 2: ASK
        'frequency': f'{frequency}',
        'setrxbw': f'{rxbw}', # default is 650
        'deviation': f'{deviation}', # default is 0
        'datarate': f'{datarate}', # default is 0
        'configmodule': '4'}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(url, data=payload, headers=headers)
    print(f"[*] Listening on frequency {frequency}")


# configure tx
def txConfig(mod, modulation, frequency, deviation, transmissions, payloads):
    url = "http://192.168.4.1/settx"
    # grab signals
    for signal in payloads:
        payload = {
            'module': f'{mod}',
            'mod': f'{modulation}',
            'transmissions': f'{transmissions}', # change as necessary
            'frequency': f'{frequency}',
            'rawdata': f'{signal}',
            'deviation': f'{deviation}',
            'configmodule': '3'}
        response = requests.post(url, data=payload)
        print(f"[$] Transmitted Successfully: \n {signal}")


# configure tesla charging port signal; sends on 315Mhz & 433.92Mhz
def teslaTx(transmissions):
    tesla = 315.00
    url = 'http://192.168.4.1/settxtesla'
    data = {'frequency': f'{tesla}', 'configmodule': '0'}
    for x in range(0, transmissions):
        response = requests.post(url, data=data)

    tesla = 433.92
    data = {'frequency': f'{tesla}','configmodule': '0'}
    for x in range(0, transmissions):
        response = requests.post(url, data=data)


# grab log file, clean up, return list of captured signals.
def formatCapture():
    payloads = []
    
    pattern = "Rawdata corrected:" 
    viewlogs = "http://192.168.4.1/viewlog"
    req = requests.get(viewlogs).text
    soup = BeautifulSoup(req, 'html.parser').get_text()
    lines = soup.splitlines()
    # grab line below each match.. such being the rawdata that is corrected
    rawdata = [i+1 for i in range(len(lines)-1) if re.search(pattern, lines[i])]
    for match in rawdata:
        data = lines[match].strip()
        # remove annoying ass html tags..
        signal = BeautifulSoup(data, 'html.parser').get_text()
        payloads.append(signal)
    return payloads

# delete & cleanspiffs 
def deleteClean():
    requests.get('http://192.168.4.1/delete', timeout=6)
    requests.get('http://192.168.4.1/cleanspiffs', timeout=6)

main()
