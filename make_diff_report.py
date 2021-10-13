
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
    min = int(sys.argv[1])
try:
    os.mkdir("reports")
except:
    pass
report_name = "reports/report_"+str(min)+"m_"+time.strftime("%B %d %H-%M")+".json"



logging.config.fileConfig('log_config.conf')
logger = logging.getLogger("MARKET")


def get_present():
    start = time.time()
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/24hr")
    except Exception:
        return False


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
    diff=last-first
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

def strategy(cryp,time_key,currency):

    last_5_avg=cryp[time_key][1]
    if last_5_avg>1.5:
        logger.error("Greter than 2 "+str(currency)+" :"+str(time_key)+":  "+str(cryp[time_key]))
        cryp["pos_trig"]=[last_5_avg,True]
    if last_5_avg<-1.5:
        logger.error("lesser than -2 "+str(currency)+" :"+str(time_key)+":  "+str(cryp[time_key]))
        cryp["neg_trig"]=[last_5_avg,True]

    if cryp["neg_trig"][1]:
        if -0.5 < last_5_avg < 0:
            logger.warning("its time to buy: "+str(currency)+" :"+str(time_key)+":  "+str(cryp[time_key]))
            cryp["neg_trig"]=[0,False]
        if last_5_avg > 0:
            logger.warning("its going up buy fast: "+str(currency)+" :"+str(time_key)+":  "+str(cryp[time_key]))
            cryp["neg_trig"]=[0,False]

    if cryp["pos_trig"][1]:
        if 0 < last_5_avg < .5:
            logger.warning("if you own this selit: "+str(currency)+" :"+str(time_key)+":  "+str(cryp[time_key]))
            cryp["pos_trig"]=[0,False]
        if  last_5_avg < 0:
            logger.warning("its falling now sell fast: "+str(currency)+" :"+str(time_key)+":  "+str(cryp[time_key]))
            cryp["pos_trig"]=[0,False]


def boot():

    with open("boot.json","r") as f:
        boot_json=json.load(f)
    print("started booy:",boot_json)
    if boot_json["started"]:
        boot_json["started"]=False
        with open("boot.json","w") as wf:
            boot_json=json.dump(boot_json, wf, sort_keys=False,indent='\t', separators=(',', ': '))
        logger.info("Found started is true, so set it false and waiting for double wait time")
        time.sleep(sec*min*2)
        with open("boot.json","r") as f:
            boot_json=json.load(f)
        if boot_json["started"]:
            logger.info("Okay its running, bye!!")
            sys.exit()
        else:
            boot_json["started"]=True
            # print(boot_json)
    else:
        boot_json["started"]=True
    print(boot_json)
    return boot_json




def main(boot_json):
    print("Hrllo")
    logger.info("Hello")
    boot_json["last_report"]=report_name
    diff = {}
    diff["started"]=time.strftime("%B %d %H:%M:%S")
    neg_keys_c=7
    tickers=0
    highest=0
    lowest=0
    while True:
        market = get_present()
        if not market:
            logger.error("some error in Connection")
            time.sleep(20)
            continue
        diff["last_updated"]=time.time()
        for coin in market:
            cryp=coin["symbol"]
            try:
                if str(cryp).endswith("usdt"):
                    prev = float(diff[cryp]["prev"])
                    last = float(market[cryp]["last"])
                    if last>diff[cryp]["range"][0]:
                        diff[cryp]["range"][0]=last
                    if last<diff[cryp]["range"][1]:
                        diff[cryp]["range"][1]=last
                    volume=diff[cryp]["volume"]=float(market[cryp]["volume"])*last
                    if prev == 0.000:
                        diff[cryp][time.strftime("%B %d %H:%M:%S")] = [0, last, last, last]
                        diff[cryp]["prev"] = last
                        continue
                    # print("got_prev", cryp)

                    diff[cryp]["change"]=get_per_change(diff[cryp]["start"],last)
                    diff[cryp]["prev"] = last
                    change = get_per_change(prev,last)
                    till_avg = 0
                    last_5_avg=0
                    if len(diff[cryp]) > neg_keys_c:
                        n=len(diff[cryp]) - neg_keys_c
                        time_key = list(diff[cryp].keys())[-1]
                        till_avg = ( ( ( n ) * float( diff[cryp][time_key][2] ) ) + change ) / ( n + 1)
                        if len(diff[cryp])- neg_keys_c >5:

                            for time_key in list(diff[cryp].keys())[-4:]:
                                last_5_avg+=diff[cryp][time_key][0]
                            last_5_avg+=change
                            last_5_avg/=5
                        else:
                            last_5_avg=till_avg
                    time_key=time.strftime("%B %d %H:%M:%S")
                    diff[cryp][time_key] = [change, last_5_avg, till_avg, last]
                    # print("volume:",market[cryp]["volume"],type(market[cryp]["volume"]))
                    if volume > 25000:
                        print("allowed",cryp)
                        strategy(diff[cryp],time_key,cryp)
                    # else:
                    #     logger.debug("OOps not good trading volume:"+str(cryp)+" "+str(market[cryp]["volume"])+" "+str(last)+" "+str(float(market[cryp]["volume"])*last))

                    if len(diff[cryp])-neg_keys_c >52:
                        key1,key2=list(diff[cryp].keys())[neg_keys_c:neg_keys_c+2]
                        diff[cryp].pop(key1)
                        diff[cryp]["start"]=diff[cryp].pop(key2)[3]



            except KeyError as e:
                logger.debug("err_key"+str(e))
                diff[cryp] = {}
                diff[cryp]["prev"] = float(market[cryp]["lastPrice"])
                diff[cryp]["start"] = float(market[cryp]["lastPrice"])
                diff[cryp]["change"] = 0
                diff[cryp]["range"]=[float(market[cryp]["lastPrice"]),float(market[cryp]["lastPrice"])]
                diff[cryp]["pos_trig"]=[0,False]
                diff[cryp]["neg_trig"]=[0,False]
                diff[cryp]["volume"]=float(market[cryp]["volume"])

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
        with open("boot.json","w") as wf:
            json.dump(boot_json, wf, sort_keys=False,indent='\t', separators=(',', ': '))
        time.sleep(10)
        # time.sleep(sec*min)

if __name__ == "__main__":
    boot_json=boot()
    main(boot_json)