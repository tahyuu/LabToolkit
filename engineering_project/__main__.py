#!/usr/bin/env python3

# Standard modules
import traceback
import sys
import logging
import time

# Functions from standard modules
from pprint import pprint
from timeit import default_timer as timer
from datetime import datetime


# Imports from modules installed by pip
import visa  # [bindings to the "Virtual Instrument Software Architecture" in order to control measurement devices and test equipment via GPIB, RS232, or USB.](https://github.com/hgrecco/pyvisa/)
#
import numpy as np  # [NumPy](http://www.numpy.org/)
import pandas as pd  # [pandas: Python Data Analysis Library](http://pandas.pydata.org/)
from openpyxl import Workbook  # [openpyxl - A Python library to read/write Excel 2010 xlsx/xlsm files — openpyxl documentation](https://openpyxl.readthedocs.io/en/default/)


# --- Import of code of RCI

# import visa_helper
from visa_helper import Instrument, ResourceManager
from visa_helper import driverdispatcher, visaenumerate, visaaddresslist

# import gitrevision

import CIS9942.parse
import File.file
from estimatedtime import estimatedtime
from pandas_helper import dfiteronrows, dflistfrequencyswithin
from immunity import leveler

import MeasurePwr

import Instrument.PowerMeter
import Instrument.SignalGenerator

# import Instrument.FunctionGenerator
'''
HP 33120A 15MHz
Keysight 33500B 20MHz
HP 8116A 50MHz
'''
# import Instrument.SignalGenerator
'''
HP 8673M 2-18GHz
Anritsu MG3710A 100e3, 6e9
Anritsu MG 10e6, 10e9
Anritsu MG 2e9, 30e9
Anritsu MG 10e6, 20e9
Agilent N5182A 100e3, 6e9
Marconi 2031 10e3-2.7e9
Marconi 20nn 10e3-5.4e9
HP 8664A 100e3, 3e9
'''
# import Instrument.PowerMeter
'''
Bird 4421
'''
# import Instrument.FieldStrength
'''
EMC-20
SI-100
EMCO 7110
'''

# import Instrument.Positioner
'''
2090 H
'''
# import Instrument.DMM
'''
HP 34401
HP 3478A
Longscale
'''
# import Instrument.NetworkAnalyser
'''
E8357A
4395A
'''
# import Instrument.SpectrumAnalyser
'''
8594E 9e3-40e9
8653E -26.5e9
E4440A 3-26.5e9
E4406A
'''
# import Instrument.Osciliscope  # TDS 544A 500e5, DSO5052A 500e6 4GSa/s
# import Instrument.SourceDC  # 6632A 0-20V 0-5A 100W
# import Instrument.SourceAC  # 3001i, 3001iM


__author__ = "David Lutton"
__license__ = "MIT"
# logging.basicConfig(level=logging.INFO)
log = logging.getLogger("RCI")  # Radiated e Conducted e Testing
log.setLevel(logging.DEBUG)
formatstr = ['asctime)', 'module)18', 'funcName)12', 'levelname)', 'message)']
formatstr = '%(' + "s - %(".join(formatstr) + 's'
formatter = logging.Formatter(formatstr)
#  %(name)s

logger = datetime.now().isoformat() + ".log"
# python3.6 isoformat(timespec='seconds')

fh = logging.FileHandler(logger)
fh.setFormatter(formatter)
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setFormatter(formatter)
ch.setLevel(logging.DEBUG)


log.addHandler(fh)
log.addHandler(ch)


# visa.log_to_screen()
log.info("Starting Radiated & Conducted Immunity")
log.info("Software by {}".format(__author__))
log.info('! EN 61000-4-6:2014')
log.info('! EN 61000-4-3:2006+A1+A2:2010')
log.info("formatstr = {}".format(formatstr))

# log.info('Git revision: ' + gitrevision.git_version()
log.info('Creating a log file in {}'.format(logger))

wb = Workbook()
ws = wb.active

with ResourceManager('Sim/default.yaml@sim') as rm:
    # 'Sim/default.yaml@sim' '@py', 'ni'

    # pool = visaenumerate(rm, rm.list_resources())
    pool = visaenumerate(rm, visaaddresslist([8, 13, 11]))

    # print(pool)
    for each in pool:
        log.info("Discovered {}".format(each))
        # log.info(each)
    log.info("Discovered {} instruments".format(len(pool)))
    log.info("Attaching drivers to recognised instruments")

    generator = driverdispatcher(pool, {
        "HEWLETT-PACKARD,8657A,": Instrument.SignalGenerator.HP8657A,
        "HEWLETT_PACKARD,8664A,": Instrument.SignalGenerator.HP8664A,
        # 8665B

        # "Agilent Technologies, E4422B,": Instrument.SignalGenerator.E4422B,
        # MG3691B 10e6, 10e9
        # MG3692, 2e9?, 20e9
        # MG3693, 2e9, 30e9
        # Willtron 10e6, 40e9
    })

    PowerMeter = driverdispatcher(pool, {
        # "Agilent Technologies, E4440A,": MeasurePwr.MeasurePwrE4440A,  # For measuring harmonics
        "HEWLETT-PACKARD,437B,": Instrument.PowerMeter.HP437B,
        # E4418B
        # NVRS
    })

    PSAPowerMeter = driverdispatcher(pool, {
        "Agilent Technologies, E4440A,": MeasurePwr.MeasurePwrE4440A,  # For measuring harmonics

    })

    log.info("Discovered " + str(len(generator)) + " SignalGenerators")
    log.info("Discovered " + str(len(PowerMeter)) + " PowerMeters")

    log.info("Discovered " + str(len(PSAPowerMeter)) + " PowerMeters")

    pprint(generator)
    pprint(PowerMeter)

    ws.append([
        "ffreqset", "ffreqmeas", "fmean", "fstdev",
        "hfreqset", "hfreqmeas", "hmean", "hstdev",
        "Generator level dBm"
        ])
    generator[0].amplimit = 10

    '''PowerMeter[0].correctionfactorinterpolateload(
                                                [100e3, 300e3, 1e6, 3e6, 10e6, 30e6, 50e6, 100e6, 300e6, 1000e6, 2000e6, 3000e6, 4200e6],
                                                [95.1, 97.6, 99.2, 98.8, 98.4, 98.2, 98, 98, 97.9, 97.5, 96.6, 95.1, 90.4]
                                                )
    print("Interpolate")
    print(PowerMeter[0].correctionfactorinterpolate(2431e6))
    '''

    # print(generator[each].instrument.query("AP?"))
    # print(PowerMeter[0].measure())
    assert len(generator) >= 1
    # assert len(PowerMeter) >= 1

    # print(dir(generator[0]))
    # print(generator[0].query("*IDN?"))
    # print(generator[0].IDN)

    '''
    Pause off tes
    Display table during test - of last ten points # pandas
    Display graph during test # matplotlib
    '''
    '''
    filetorunharmonicscheckagainst = File.file.fileopen(title="File to run harmonics check against", filetypes=(("CAL files", "*.CAL;*.cal"), ("All files", "*.*")))
    # filetorunharmonicscheckagainst = "Dataset/20170113-K/CALS/140115V7.CAL"
    print(filetorunharmonicscheckagainst)

    with open(filetorunharmonicscheckagainst, 'r') as f:
        df = CIS9942.parse.parse(f.readlines())
        # print(df)
        with pd.option_context('display.max_rows', 1024):
            pass
            # print(df)
        print()
        print()

    # for step in dfiteronrows(df):
        # print(step['Frequency'])
        # print(step)

    # print(dflistfrequencyswithin(df))

    rowsource = dfiteronrows(df)

    EstimatedTime = ETA.estimatedtime(len(df))
    # EstimatedTime.append(10)
    # EstimatedTime.append(19)

    try:
        generator[0].start()

        for row, index in rowsource:
            start = timer()
            print()
            print()
            print(row)
            print()
            print(index)

            print(index)
            print(row)

            # time.sleep(1)

            freq = row['Frequency']
            print()
            print(row['Generator Level'])

            generator[0].freq(row['Frequency'])

            # freqmeas, amp = PowerMeter.measure(freq)
            # couplingoffsetfromCISsetup = ((-0.0000000024 * int(freq)) + 40.4)
            # couplingoffsetfromCISsetup = 30
            # couplingdelta = couplingoffsetfromCISsetup - couplingoffsetfromdirectmeasurements

            # couplingoffset = couplingdelta + couplingoffsetfromCISsetup
            # expectedpower = float(row["Forward Power"]) - couplingoffset
            # print(round(expectedpower, ndigits=2))

            measure = False

            while measure is not True:
                errorpwr, errorcent, newlevel = leveler(
                        PowerMeter[0].measure(),
                        float(row['Forward Power'])-50.0,
                        generator[0].amplitude,
                )
                print(newlevel)
                generator[0].ampsetter(newlevel)
                print("Error Power " + str(errorpwr))
                if 0.1 >= errorpwr >= -0.1:
                    measure = True
                    ###### generator[0].lvl
                    time.sleep(1)  # Settling time

                    measurements = []
                    measurementfreq = []

                    freqmeas, amp = PSAPowerMeter[0].measure(freq)
                    PSAPowerMeter[0].reflvl(float(amp) + 10)

                    for reads in range(5):
                        time.sleep(.1)
                        freqmeas, amp = PSAPowerMeter[0].measure(freq)

                        # measurements[reads] = {float(freq): float(amp)}
                        measurements.append(float(amp))
                        measurementfreq.append(float(freqmeas))
                    # pprint(measurements)

                    result = {
                        "freqset": freq,
                        "freqmeas": numpy.mean(measurementfreq),
                        "mean":  numpy.mean(measurements),
                        "stdev": numpy.std(measurements),
                    }
                    pprint(result)
                    with open("testfund" + ".csv", "a") as file:
                        file.write(
                            str(result["freqset"]) + ", " +
                            str(result["freqmeas"]) + ", " +
                            str(result["mean"]) + ", " +
                            str(result["stdev"]) + "\n")
                    print("")
                    fundementalresult = result

                    measurements = []
                    measurementfreq = []
                    meas = float(freqmeas) * 3
                    for reads in range(5):
                        time.sleep(.1)
                        freqmeas, amp = PSAPowerMeter[0].measure(meas)

                        # measurements[reads] = {float(freq): float(amp)}
                        measurements.append(float(amp))
                        measurementfreq.append(float(freqmeas))
                    # pprint(measurements)

                    result = {
                        "freqset": freq,
                        "freqmeas": numpy.mean(measurementfreq),
                        "mean":  numpy.mean(measurements),
                        "stdev": numpy.std(measurements),
                    }
                    pprint(result)
                    harmonicresult = result

                    with open("testharm" + ".csv", "a") as file:
                        file.write(
                            str(result["freqset"]) + ", " +
                            str(result["freqmeas"]) + ", " +
                            str(result["mean"]) + ", " +
                            str(result["stdev"]) + "\n")
                    print()

                    ws.append([
                        fundementalresult["freqset"],
                        fundementalresult["freqmeas"],
                        fundementalresult["mean"],
                        fundementalresult["stdev"],
                        harmonicresult["freqset"],
                        harmonicresult["freqmeas"],
                        harmonicresult["mean"],
                        harmonicresult["stdev"]
                        ])

            EstimatedTime.append(timer() - start)  # end - start
            print("ETA: " + str(EstimatedTime.ETA()) + " s")
            print()

    finally:
        generator[0].safe()
        generator[0].disable()
        wb.save("test" + ".xlsx")
    '''
