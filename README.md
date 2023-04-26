# EvilCrowPyRF
Simple python script to Receive/Transmit/Save Evil Crow RF log files 📡


# Install
```
# if using a pc or of that sort
git clone https://GitHub.com/CharlesTheGreat77/EvilCrowPyRF
cd EvilCrowPyRF
pip3 install -r requirements.txt

# Pyto (iOS) PyPI packages
install bs4 (beautifulsoup)
```

# usage
Configure receiver on freq. 433.92 with rxbw of 650 (default is 650), ASK modulation (default no need to specify), deviation 0 (default), data rate to 5 (default).  
```
python3 ecrf.py -rx -f 433.92 --rxbw 650
```

Configure reciever on freq. 434.07, deviation of 47.6, 2FSK modulation (-m 1), using module 2 [default] (ONLY RX ON MODULE 2 for FSK)
```
python3 ecrf.py -rx -f 434.07 -d 47.6 -mod 2 -m 1
```

Save logs to output file (one can specify modulation and frequency to add to output, if not, input will be asked)
```
python3 ecrf.py -o logs/frontGate.txt [-f <frequency>] [-m <modulation>] [-d <deviation>]
```

Transmit signals in logs two times on freq. 315.00, 2FSK (-m 1), with a deviation of 47.6, using module 1 on ECRF
```
python3 ecrf.py -tx -f 315.00 -m 1 -d 47.6 -mod 1 -t 2
```

Transmit signals in saved files
```
python3 --txoutput logs/frontGate.txt
```

Transmit Tesla signals
```
python3 ecrf.py --tesla
```
# Evil Crow RF
https://github.com/joelsernamoreno/EvilCrowRF-V2
