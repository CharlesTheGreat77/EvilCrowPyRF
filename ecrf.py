import argparse
import requests
from bs4 import BeautifulSoup
import re, time


def main():
    parser = argparse.ArgumentParser(description='Control ECRF v2 with Python!!')
    parser.add_argument('-f', '--frequency', type=float, required=False, help='frequency in MHz')
    parser.add_argument('-d', '--deviation', type=float, default=0, help='deviation in kHz [default: 0]')
    parser.add_argument('-mod', '--module', type=int, default=2, help='module number [module 1, module 2]')
    parser.add_argument('-m', '--modulation', type=int, default=2, help='modulation type [1: 2FSK, 2: ASK]')
    parser.add_argument('-t', '--transmissions', type=int, default=1, help='number of transmissions [default: 1]')
    parser.add_argument('-rxbw', '--rxbw', type=float, default=650.00, help='set rxbw [default: 650.00]')
    parser.add_argument('-dr', '--datarate', type=float, default=3.79, help='datarate [default: 3.79]')
    parser.add_argument('-rx', '--rxconfig', help='configure rx mode', action='store_true')
    parser.add_argument('-tx', '--txconfig', help='configure tx mode', action='store_true')
    parser.add_argument('-tesla', '--tesla', help='sends tesla charging port signal', action='store_true')
    parser.add_argument('-btn', '--button', help='set payload(s) to button (button: 1, button: 2)', type=int, required=False)
    parser.add_argument('-j', '--jammer', help='enable jammer (use -f to specify frequency & -p for power level)', action='store_true')
    parser.add_argument('-p', '--power', help='specify power level of jammer (1-10) [default: 5]', type=int, default=5)
    parser.add_argument('-timer', '--timer', help='specify stop time for jammer [default: 10 seconds]', type=int, default=10)
    parser.add_argument('--delete', help='delete logs/cleanspiffs', action='store_true')
    parser.add_argument('-o', '--output', help='specify output file for captured logs', type=str, required=False)
    parser.add_argument('-file', '--file', help='specify previously saved files (use -tx to transmit)', required=False, type=str)

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
    button = args.button
    jammer = args.jammer
    power = args.power
    timer = args.timer
    delete = args.delete
    txfile = args.file
    output = args.output
    payloads = None


    # send tesla signals
    if tesla:
        print("[*] Opening charging port..")
        teslaTx(transmissions)

    if delete:
        print('[*] Deleting logs and cleaning spiffs')
        deleteClean()

    if output != None:
        print(f'[*] Saving logs to {output}')
        payloads = formatCapture()
        # if frequency etc. is not specified when -o is passed, ask for input
        if frequency == None:
            frequency = float(input(f'[*] Enter the frequency the logs are operating on: '))
            modulation = input(f'[*] Enter the modulation the logs are operating on [FSK/ASK]: ')
            if 'FSK' in modulation or 'fsk' in modulation:
                deviation = float(input(f'[*] Enter the deviation the logs are operating on: '))

        # file format for saved signals
        with open(output, 'w') as file:
            file.write(f'Frequency: {frequency}\n')
            file.write(f'Modulation: {modulation}\n')
            file.write(f'Deviation: {deviation}\n')
            for payload in payloads:
                file.write(f'Payload: {payload}\n')

    if jammer:
        simpleJam(mod, frequency, power, timer)

    # if file is passed, grab config settings and payloads
    if txfile != None:
        frequency, modulation, deviation, payloads = formatFile(txfile)
        print(f"Frequency: {frequency}\nModulation: {modulation}\nDeviation: {deviation}")

    # set payloads to button if specified
    if button != None:
        if payloads == None:
            payloads = formatCapture()
        buttonTx(frequency, modulation, deviation, payloads, button, transmissions)

    if txconfig:
        # grab logs if no payloads are in list
        if payloads == None:
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
        'datarate': f'{datarate}', # default is 5
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
        print(f"[$] Transmittion Successful: \n {signal}")


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

def buttonTx(frequency, modulation, deviation, payloads, button, transmissions):
    url = "http://192.168.4.1/setbtn"
    for payload in payloads:
        setBtn = {
            "button":f"{button}",
            "mod": f"{modulation}",
            "transmissions": f"{transmissions}",
            "frequency": f"{frequency}",
            "rawdata": f"{payload}",
            "deviation": f"{deviation}"
        }
        req = requests.post(url, data=setBtn)
        print(f"[$] Button {button} set to:\n{payload.rstrip()}")
        input("[PRESS ENTER TO CONTINUE WITH THE NEXT SIGNAL]")

def simpleJam(mod, frequency, power, timer):
    url = 'http://192.168.4.1/setjammer'
    payload = {
        "module": f"{mod}",
        "frequency": f"{frequency}",
        "setpower": f"{power}"
    }
    print(f"[*] Starting jammer on {frequency}Mhz")
    req = requests.post(url, data=payload)
    # jam for x seconds
    time.sleep(timer)
    print(f'[*] Stopping jammer..')
    req = request.post("http://192.168.4.1/stopjammer")

# grab log file, clean up, return list of captured signals.
def formatCapture():
    payloads = []
    viewlogs = "http://192.168.4.1/viewlog"
    req = requests.get(viewlogs).text
    signals = []
    for signal in req.split('Count=')[1:]:
        signal_data = signal.split('<br>')[1]
        signals.append(signal_data)
    
    for data in signals:
        # rawdata corrected was not sending signal correctly
        if 'Rawdata' in data:
            continue
        else:
            payloads.append(data)
    return payloads

# grab config settings and payload in file
def formatFile(txfile):
    payloads = []
    with open(txfile, 'r') as file:
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
                payload = line.split(':')[1].strip()
                payloads.append(payload)
    return frequency, modulation, deviation, payloads

# delete & cleanspiffs 
def deleteClean():
    requests.get('http://192.168.4.1/delete', timeout=6)
    requests.get('http://192.168.4.1/cleanspiffs', timeout=6)

main()
