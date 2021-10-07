
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
import json,time,os
import logging
import logging.config

sec=60
min=30
try:
    os.mkdir("reports")
except:
    pass
report_name="reports/report_"+time.strftime("%B %d %H-%M")+".json"

logging.config.fileConfig('log_config.conf')
logger = logging.getLogger("MARKET")
def get_present():
    start=time.time()
    res=requests.get("https://api.wazirx.com/api/v2/tickers")

    if res.ok:
        market=res.json()
        end=time.time()
        logger.info("req time:"+ str(int(end-start))+ " sec")
        return market
    else:
        return False

if __name__=="__main__":
    print("Hrllo")
    logger.info("Hello")
    diff={}
    while True:
        market=get_present()
        if not market:
            print("some error")
        for cryp in market:
            try:
                if str(cryp).endswith("inr"):
                    prev=float(diff[cryp]["prev"])
                    last=float(market[cryp]["last"])
                    if prev<=0.000:
                        diff[cryp][time.strftime("%B %d %H:%M:%S")]=[0,last/2,last]
                        diff[cryp]["prev"]=last
                        continue
                    print("got_prev",cryp)

                    diff[cryp]["prev"]=last
                    change=((last-prev)/prev)*100
                    till_avg=0
                    if len(diff[cryp])>1:
                        # print("lis_fist_item",list(diff[cryp].keys())[-1][0])
                        time_key=list(diff[cryp].keys())[-1]
                        # print(cryp,time_key,diff[cryp][time_key],type(diff[cryp][time_key]),sep=", ")
                        till_avg=(float(diff[cryp][time_key][0])+change)/2
                    diff[cryp][time.strftime("%B %d %H:%M:%S")]=[change,till_avg,last]
            except KeyError as e:
                logger.exception("err_key"+str(e))
                diff[cryp]={}
                diff[cryp]["prev"]=market[cryp]["last"]

        with open(report_name, 'w') as outfile:
            json.dump(diff, outfile, sort_keys=False, indent='\t', separators=(',', ': '))
            print("Added_to_file")



        time.sleep(sec*min)
        # time.sleep(10)


