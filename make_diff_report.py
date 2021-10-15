
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
import trade

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

def get_per(principle,percentage):
    return principle * ((100 + percentage)/ 100)

def strategy(cryp,time_key,currency):

    last_5_avg=cryp[time_key][1]
    if last_5_avg>1.7:
        logger.error("Greter than 2 "+str(currency)+" :"+str(time_key)+":  "+str(cryp[time_key]))
        cryp["pos_trig"]=[last_5_avg,True]
    if last_5_avg<-1.7:
        logger.error("lesser than -2 "+str(currency)+" :"+str(time_key)+":  "+str(cryp[time_key]))
        cryp["neg_trig"]=[last_5_avg,True]

    if cryp["neg_trig"][1]:
        if -0.3 < last_5_avg:
            logger.warning("its buy time: "+str(currency)+" "+str(cryp[time_key][3])+":"+str(time_key)+":  "+str(cryp[time_key]))
            if cryp["change"]>50:
                logger.error("Tooo much +ve change in a day, rejecting buy:"+str(cryp["change"])+"%")
                return
            try:
                trade.buy(currency, float(str(get_per(cryp[time_key][3],-0.2))[:len(str(cryp[time_key][3]))]))
            except Exception as e:
                logger.exception("Buy order exception:"+ str(e))
            cryp["neg_trig"]=[0,False]

    if cryp["pos_trig"][1]:
        if last_5_avg < .3:
            logger.warning("if you own this selit: "+str(currency)+" "+str(cryp[time_key][3])+":"+str(time_key)+":  "+str(cryp[time_key]))
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

def get_last24(diff):
    logger.info("Getting the last 24hr data")
    try:
        exchanges = requests.get("https://api.binance.com/api/v1/exchangeInfo")
    except Exception:
        logger.exception("OOOOHH SHIET")
        sys.exit()
    neg_keys_c=7
    volume_thres=600000
    if exchanges.ok:
        exchanges = exchanges.json()
        with open("exchanges.json","w") as wf:
           json.dump(exchanges, wf, sort_keys=False,indent='\t', separators=(',', ': '))
        for currency in exchanges['symbols']:
            print(currency['symbol'])
            symbol=currency['symbol']
            if not str(symbol).endswith("USDT"):
                continue
            if re.search("[A-Z]+DOWNUSDT",symbol) or re.search("[A-Z]+UPUSDT",symbol):
                continue
            time.sleep(0.5)
            try:
                past_tickers = requests.get("https://api.binance.com/api/v3/klines?symbol="+str(symbol)+"&interval=15m&startTime="+str(int((time.time()- 86400)*1000))+"&endTime="+str(int(time.time()*1000)))
            except Exception:
                logger.exception("ticker_problem")
                continue


            if past_tickers.ok:
                tickers =list(past_tickers.json())
            for ticker in tickers:
                cryp=symbol
                try:
                    if str(cryp).endswith("USDT"):
                        if re.search("[A-Z]+DOWNUSDT",cryp) or re.search("[A-Z]+UPUSDT",cryp):
                            continue
                        prev = float(diff[cryp]["prev"])
                        last = float(ticker[4])
                        if last>diff[cryp]["range"][0]:
                            diff[cryp]["range"][0]=last
                        if last<diff[cryp]["range"][1]:
                            diff[cryp]["range"][1]=last
                        volume=diff[cryp]["volume"]=float(ticker[5])*last
                        if prev == 0.000:
                            diff[cryp][time.strftime("%B %d %H:%M:%S",time.gmtime((ticker[0]/1000)+19800))] = [0, last, last, last]
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
                        # print(ticker)
                        time_key=time.strftime("%B %d %H:%M:%S",time.gmtime((ticker[0]/1000)+19800))
                        diff[cryp][time_key] = [change, last_5_avg, till_avg, last]


                        if len(diff[cryp])-neg_keys_c >52:
                            key1,key2=list(diff[cryp].keys())[neg_keys_c:neg_keys_c+2]
                            diff[cryp].pop(key1)
                            diff[cryp]["start"]=diff[cryp].pop(key2)[3]
                except KeyError as e:
                    logger.debug("err_key"+str(e))
                    diff[cryp] = {}
                    diff[cryp]["prev"] = float(ticker[4])
                    diff[cryp]["start"] = float(ticker[4])
                    diff[cryp]["change"] = 0
                    diff[cryp]["range"]=[float(ticker[4]),float(ticker[4])]
                    diff[cryp]["pos_trig"]=[0,False]
                    diff[cryp]["neg_trig"]=[0,False]
                    diff[cryp]["volume"]=float(ticker[5])*float(ticker[4])
            # break
    time.sleep(5*60)
    return diff

    # sys.exit()


def main(boot_json):
    print("Hrllo")
    logger.info("Hello")
    boot_json["last_report"]=report_name
    diff = {}
    diff["started"]=time.strftime("%B %d %H:%M:%S")
    neg_keys_c=7
    tickers=0
    volume_thres=600000
    diff["last_updated"]=time.time()
    diff = get_last24(diff)
    logger.info("Got last 24hr dtaa")

    while True:
        diff["last_updated"]=time.time()

        market = get_present()
        if not market:
            logger.error("some error in Connection")
            time.sleep(20)
            continue

        for coin in market:
            cryp=coin["symbol"]
            # print(cryp)
            try:
                if str(cryp).endswith("USDT"):
                    if re.search("[A-Z]+DOWNUSDT",cryp) or re.search("[A-Z]+UPUSDT",cryp):
                        continue
                    prev = float(diff[cryp]["prev"])
                    last = float(coin["lastPrice"])
                    if last>diff[cryp]["range"][0]:
                        diff[cryp]["range"][0]=last
                    if last<diff[cryp]["range"][1]:
                        diff[cryp]["range"][1]=last
                    volume=diff[cryp]["volume"]=float(coin["volume"])*last
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
                    # print("volume:",coin["volume"],type(coin["volume"]))
                    if volume > volume_thres:
                        # print("allowed",cryp,volume)
                        strategy(diff[cryp],time_key,cryp)
                    else:
                        print("allowed",cryp,volume)
                    #     logger.debug("OOps not good trading volume:"+str(cryp)+" "+str(coin["volume"])+" "+str(last)+" "+str(float(coin["volume"])*last))

                    if len(diff[cryp])-neg_keys_c >52:
                        key1,key2=list(diff[cryp].keys())[neg_keys_c:neg_keys_c+2]
                        diff[cryp].pop(key1)
                        diff[cryp]["start"]=diff[cryp].pop(key2)[3]



            except KeyError as e:
                logger.debug("err_key"+str(e))
                diff[cryp] = {}
                diff[cryp]["prev"] = float(coin["lastPrice"])
                diff[cryp]["start"] = float(coin["lastPrice"])
                diff[cryp]["change"] = 0
                diff[cryp]["range"]=[float(coin["lastPrice"]),float(coin["lastPrice"])]
                diff[cryp]["pos_trig"]=[0,False]
                diff[cryp]["neg_trig"]=[0,False]
                diff[cryp]["volume"]=float(coin["volume"])*float(coin["lastPrice"])

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
        # time.sleep(10)
        time.sleep(sec*min)

if __name__ == "__main__":
    boot_json=boot()
    try:
        main(boot_json)
    except KeyboardInterrupt:
        boot_json["started"]=False
        with open("boot.json","w") as wf:
            json.dump(boot_json, wf, sort_keys=False,indent='\t', separators=(',', ': '))