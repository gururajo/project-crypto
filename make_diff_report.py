
#!/usr/bin/python

###############################################################################
#
# Authors:
# Gururaj Otageri <gururajotagerimail2@gmail.com>
#
# Date: 10/06/2021
#
# Version 1.0 - Requirement python >3.x
#
# Copyright:
# Copyright (C) 2021 TBD , http://www.TBD.com
#
###############################################################################

import requests
import re
import json
import time
import os
import logging,sys
import logging.config

sec = 60
min = 15
if len(sys.argv)==2:
    min = sys.argv[1]
try:
    os.mkdir("reports")
except:
    pass
report_name = "reports/report_"+str(min)+"s_"+time.strftime("%B %d %H-%M")+".json"



logging.config.fileConfig('log_config.conf')
logger = logging.getLogger("MARKET")


def get_present():
    start = time.time()
    res = requests.get("https://api.wazirx.com/api/v2/tickers")

    if res.ok:
        market = res.json()
        end = time.time()
        logger.info("req time:" + str(int(end-start)) + " sec")
        return market
    else:
        return False

def get_per_change(first,last):

    if first==0:
        return last
    diff=first-last
    per=(diff/first)*100
    return per

def align_report(report):
    # print(report)
    # time.sleep(5)
    report=re.sub("\[\\n			","[ ",report)
    # print(report)
    # time.sleep(20)
    report=re.sub("\\n			"," ",report)
    report=re.sub("\\n		\]"," ]",report)
    return report


if __name__ == "__main__":
    print("Hrllo")
    logger.info("Hello")
    diff = {}
    neg_keys_c=3
    tickers=0
    while True:
        market = get_present()
        if not market:
            print("some error")
        for cryp in market:
            try:
                if str(cryp).endswith("inr"):
                    prev = float(diff[cryp]["prev"])
                    last = float(market[cryp]["last"])
                    if prev <= 0.000:
                        diff[cryp][time.strftime("%B %d %H:%M:%S")] = [0, last/2, last]
                        diff[cryp]["prev"] = last
                        continue
                    print("got_prev", cryp)

                    diff[cryp]["change"]=get_per_change(diff[cryp]["start"],last)
                    diff[cryp]["prev"] = last
                    change = ((last-prev)/prev)*100
                    till_avg = 0
                    if len(diff[cryp]) > neg_keys_c:
                        # print("lis_fist_item",list(diff[cryp].keys())[-1][0])
                        time_key = list(diff[cryp].keys())[-1]
                        # print(cryp,time_key,diff[cryp][time_key],type(diff[cryp][time_key]),sep=", ")
                        till_avg = ( ( ( len(diff[cryp]) - neg_keys_c ) * float( diff[cryp][time_key][1] ) ) + change ) / ( len(diff[cryp]) - neg_keys_c + 1)
                    diff[cryp][time.strftime("%B %d %H:%M:%S")] = [
                        change, till_avg, last]
            except KeyError as e:
                logger.debug("err_key"+str(e))
                diff[cryp] = {}
                diff[cryp]["prev"] = float(market[cryp]["last"])
                diff[cryp]["start"] = float(market[cryp]["last"])
                diff[cryp]["change"] = 0

        with open(report_name, 'w') as outfile:
            json.dump(diff, outfile, sort_keys=False,
                      indent='\t', separators=(',', ': '))
            print("Added_to_file")
        if tickers>5:
            with open(report_name, "r") as f:
                report=f.read()
            report= align_report(report)
            with open(report_name, "w") as wf:
                wf.write(report)
        tickers+=1
        if tickers>10:
            with open("temp", "w") as wf:
                wf.write(str(diff))
            sys.exit()
        # time.sleep(sec*min)
        time.sleep(10)
