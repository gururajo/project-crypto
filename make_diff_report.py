
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
neg_keys_c=8
cron =False
buys_done=0

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

def create_market_cap_data():
    try:
        exchange=requests.get("https://api.binance.com/api/v3/ticker/24hr").json()
    except Exception:
        return {"last_updated":0,"symbols":{}}
    try:
        market_cap=requests.get("https://www.binance.com/exchange-api/v2/public/asset-service/product/get-products").json()["data"]
    except Exception:
        return {"last_updated":0,"symbols":{}}
    result_data={}
    for coin in exchange:
        symbol=str(coin["symbol"])
        if not symbol.endswith("USDT"):
            continue
        symbol=symbol.replace("USDT","")
        if symbol.endswith("UP") or symbol.endswith("DOWN") or symbol.endswith("BULL") or symbol.endswith("BEAR"):
            continue
        for c in market_cap:
            if c["s"]==symbol+"USDT":
                try:
                    result_data[symbol+"USDT"]=float(c["cs"])*float(coin["lastPrice"])
                    break
                except Exception:
                    continue
        else:
            logger.warning("Not found in B data "+str(symbol))
    with open("market_cap_data.json","w") as wf:
        json.dump({"last_updated":time.time(),"symbols": result_data },wf, sort_keys=False,indent='\t', separators=(',', ': '))
    return {"last_updated":time.time(),"symbols": result_data }

def get_market_cap(symbol):
    try:
        with open("market_cap_data.json","r") as f:
            market_cap=json.load(f)
    except Exception:
        logger.info("Market_cap data not available. creating new")
        market_cap=create_market_cap_data()
    if market_cap["last_updated"] < (time.time()- (24*60*60)):
        logger.info("Market_cap data invalid npw. creating new")
        market_cap=create_market_cap_data()
    try:
        return market_cap["symbols"][symbol]
    except Exception:
        logger.error("symbol market cap not found"+str(symbol))
        return 0

def strategy(cryp,time_key,currency):
    global buys_done
    last_5_avg=cryp[time_key][1]

    # if last_5_avg>1.3:
    #     logger.error("Greter than 2 "+str(currency)+" :"+str(time_key)+":  "+str(cryp[time_key]))
    #     cryp["pos_trig"]=[last_5_avg,True]
    #     return True
    if last_5_avg<-1.5:
        logger.error("lesser than -1.5 "+str(currency)+" :"+str(time_key)+":  "+str(cryp[time_key]))
        cryp["neg_trig"]=[last_5_avg,True]
        return True
    last_3_avg=last_n_avg(cryp,3)

    if cryp["neg_trig"][1]:
        if -0.4 < last_3_avg < 0.5 and last_5_avg < -0.8:
            logger.warning("its buy time: "+str(currency)+" "+str(cryp[time_key][3])+":"+str(time_key)+":  "+str(cryp[time_key]))
            if cryp["change"]> 15 or cryp["change_24hr"]>15:
                logger.error("Tooo much +ve change in a day, rejecting buy:"+str(cryp["change"])+"%")
                cryp["neg_trig"]=[0,False]
                return None
            try:
                if buys_done>2:
                    logger.info("3 orders already created in this session")
                    return None
                if get_market_cap(currency) < 45000000:
                    logger.info("lesser than threshold market cap, rejecting buy")
                    cryp["neg_trig"]=[0,False]
                    return None
                if cryp[time_key][0] > 1:
                    logger.info("change is greter than 1%, not a good time to buy")
                    # cryp["neg_trig"]=[0,False]
                    return None
                if cryp["volume"]< 2500000:
                    logger.info("lesser than threshold volume (2.5m), rejecting buy")
                    cryp["neg_trig"]=[0,False]
                    return None
                order=trade.buy(currency, get_per(cryp[time_key][3],-0.2),cryp=cryp)
                if not order:
                    logger.info("Damn order didnt complete")
                    return None
                buys_done+=1
            except Exception as e:
                logger.exception("Buy order exception:"+ str(e))
                return None
            cryp["neg_trig"]=[0,False]
        # elif -0.4 < last_3_avg :
        #     logger.warning("Last 3 avg is greater than -0.4 but last_5_avg is not < -0.45: "+str(currency)+" "+str(cryp[time_key][3])+":"+str(time_key)+":  "+str(cryp[time_key]))
        elif last_3_avg >2:
            # logger.warning("last 3 avg > 3%")
            cryp["neg_trig"]=[0,False]
            logger.warning("last 3 avg greater than 2, setting false "+str(currency)+" "+str(cryp[time_key][3])+":"+str(time_key)+":  "+str(cryp[time_key]))
    # if cryp["pos_trig"][1]:
    #     if last_5_avg < .3:
    #         logger.warning("if you own this selit: "+str(currency)+" "+str(cryp[time_key][3])+":"+str(time_key)+":  "+str(cryp[time_key]))
    #         cryp["pos_trig"]=[0,False]
    return True

def boot():
    global min,sec
    try:
        with open("boot.json","r") as f:
            boot_json=json.load(f)
    except Exception:
        logger.exception("Booot file currupted, recovering from backup")
        with open("boot_bk.json","r") as f:
            boot_json=json.load(f)
    print("started booy:",boot_json)
    if boot_json["started"]:
        boot_json["started"]=False
        with open("boot.json","w") as wf:
            boot_json=json.dump(boot_json, wf, sort_keys=False,indent='\t', separators=(',', ': '))
        logger.info("Found started is true, so set it false and waiting for double wait time")
        time.sleep(sec*(min+15))
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

def last_n_avg(cryp,n):
    n_avg=0
    for time_key in list(cryp.keys())[-1*n:]:
        n_avg+=cryp[time_key][0]
    n_avg/=n
    return n_avg

def get_last24(diff):
    logger.info("Getting the last 24hr data")
    try:
        exchanges = requests.get("https://api.binance.com/api/v1/exchangeInfo")
    except Exception:
        logger.exception("OOOOHH SHIET")
        sys.exit()
    global neg_keys_c
    if exchanges.ok:
        exchanges = exchanges.json()
        with open("exchange.json","w") as wf:
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
                            time_key=time.strftime("%B %d %H:%M:%S",time.gmtime((ticker[0]/1000)+19800))
                            if len(diff[cryp])- neg_keys_c >7:
                                diff[cryp][time_key] = [change, 0,0, last]
                                diff[cryp][time_key] = [change, last_n_avg(diff[cryp],7),last_n_avg(diff[cryp],len(diff[cryp])-neg_keys_c), last]
                            else:
                                diff[cryp][time_key] = [change,till_avg,till_avg , last]
                        else:
                            time_key=time.strftime("%B %d %H:%M:%S",time.gmtime((ticker[0]/1000)+19800))
                            diff[cryp][time_key] = [change,till_avg,till_avg , last]
                        # print(ticker)



                        if len(diff[cryp])-neg_keys_c >96:
                            key1,key2=list(diff[cryp].keys())[neg_keys_c:neg_keys_c+2]
                            diff[cryp].pop(key1)
                            diff[cryp]["start"]=diff[cryp].pop(key2)[3]
                except KeyError as e:
                    # logger.debug("err_key"+str(e))
                    diff[cryp] = {}
                    diff[cryp]["prev"] = float(ticker[4])
                    diff[cryp]["start"] = float(ticker[4])
                    diff[cryp]["change"] = 0
                    diff[cryp]["change_24hr"] = 0
                    diff[cryp]["range"]=[float(ticker[4]),float(ticker[4])]
                    diff[cryp]["pos_trig"]=[0,False]
                    diff[cryp]["neg_trig"]=[0,False]
                    diff[cryp]["volume"]=float(ticker[5])*float(ticker[4])
            # break
    # time.sleep(5*60)
    return diff

    # sys.exit()


def main(boot_json):
    print("Hrllo")
    logger.info("Hello")
    boot_json["last_report"]=report_name
    diff = {}
    diff["started"]=time.strftime("%B %d %H:%M:%S")
    global neg_keys_c,cron
    global min,sec,buys_done
    tickers=0
    volume_thres=1000000
    diff["last_updated"]=time.time()
    if time.time()-boot_json["market_15min"][1]< min*sec:
        logger.info("Looks like recent old report is available,waiting for "+str((min*sec-(time.time()-boot_json["market_15min"][1]))/sec)+" min")
        boot_json["started"]=True

        try:
            with open(boot_json["market_15min"][0],"r") as f:
                diff=json.load(f)
        except FileNotFoundError:
            logger.error("File not found!!!!")
            boot_json["started"]=False
            boot_json["market_15min"][1]=-1
            with open("boot.json","w") as wf:
                json.dump(boot_json, wf, sort_keys=False,indent='\t', separators=(',', ': '))
            sys.exit()
        else:
            with open("boot.json","w") as wf:
                json.dump(boot_json, wf, sort_keys=False,indent='\t', separators=(',', ': '))
        time.sleep(min*sec-(time.time()-boot_json["market_15min"][1]))
    elif boot_json["market_15min"][1]>0:
        boot_json["started"]=False
        boot_json["market_15min"][1]=-1
        logger.info("recent old report is invalid now, exiting")
        with open("boot.json","w") as wf:
            json.dump(boot_json, wf, sort_keys=False,indent='\t', separators=(',', ': '))
        sys.exit()
    elif cron:
        time.sleep(100)
        diff = get_last24(diff)
    else:
        logger.info("Not cron call, exiting")
        sys.exit()
    logger.info("Got last 24hr dtaa")

    while True:
        diff["last_updated"]=time.time()
        buys_done=0
        market = get_present()
        if not market:
            logger.error("some error in Connection")
            with open("boot.json","r") as f:
                boot_json=json.load(f)
            boot_json["started"]=True
            with open("boot.json","w") as wf:
                json.dump(boot_json, wf, sort_keys=False,indent='\t', separators=(',', ': '))
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
                    diff[cryp]["change_24hr"] = float(coin["priceChangePercent"])
                    diff[cryp]["prev"] = last
                    change = get_per_change(prev,last)
                    till_avg = 0
                    last_5_avg=0
                    if len(diff[cryp]) > neg_keys_c:
                        n=len(diff[cryp]) - neg_keys_c
                        time_key = list(diff[cryp].keys())[-1]
                        till_avg = ( ( ( n ) * float( diff[cryp][time_key][2] ) ) + change ) / ( n + 1)
                        time_key=time.strftime("%B %d %H:%M:%S")
                        if len(diff[cryp])- neg_keys_c >7:
                            diff[cryp][time_key] = [change, 0,0, last]
                            diff[cryp][time_key] = [change, last_n_avg(diff[cryp],7),last_n_avg(diff[cryp],len(diff[cryp])-neg_keys_c), last]
                        else:
                            diff[cryp][time_key] = [change,till_avg,till_avg , last]
                    else:
                        time_key=time.strftime("%B %d %H:%M:%S")
                        diff[cryp][time_key] = [change,till_avg,till_avg , last]
                    # print("volume:",coin["volume"],type(coin["volume"]))
                    if volume > volume_thres and len(list(diff[cryp].keys()))-neg_keys_c>9:
                        # print("allowed",cryp,volume)
                        if strategy(diff[cryp],time_key,cryp)==None:
                            logger.info("Buy didn't complete ,next timemayb")
                    else:
                        print("not allowed",cryp,volume)
                    #     logger.debug("OOps not good trading volume:"+str(cryp)+" "+str(coin["volume"])+" "+str(last)+" "+str(float(coin["volume"])*last))

                    if len(diff[cryp])-neg_keys_c >69:
                        key1,key2=list(diff[cryp].keys())[neg_keys_c:neg_keys_c+2]
                        diff[cryp].pop(key1)
                        diff[cryp]["start"]=diff[cryp].pop(key2)[3]



            except KeyError as e:
                logger.debug("err_key"+str(e))
                diff[cryp] = {}
                diff[cryp]["prev"] = float(coin["lastPrice"])
                diff[cryp]["start"] = float(coin["lastPrice"])
                diff[cryp]["change"] = 0
                diff[cryp]["change_24hr"] = float(coin["priceChangePercent"])
                diff[cryp]["range"]=[float(coin["lastPrice"]),float(coin["lastPrice"])]
                diff[cryp]["pos_trig"]=[0,False]
                diff[cryp]["neg_trig"]=[0,False]
                diff[cryp]["volume"]=float(coin["volume"])*float(coin["lastPrice"])

        with open(report_name, 'w') as outfile:
            json.dump(diff, outfile, sort_keys=False,
                      indent='\t', separators=(',', ': '))
            print("Added_to_file")
        if tickers>1:
            with open(report_name, "r") as f:
                report=f.read()
            report= align_report(report)
            with open(report_name, "w") as wf:
                wf.write(report)
        tickers+=1
        with open("boot.json","r") as f:
            boot_json=json.load(f)
        boot_json["started"]=True
        boot_json["last_report"]=report_name
        boot_json["market_15min"]=[report_name,time.time()]

        with open("boot.json","w") as wf:
            json.dump(boot_json, wf, sort_keys=False,indent='\t', separators=(',', ': '))
        # time.sleep(10)
        time.sleep(sec*min)

if __name__ == "__main__":
    time.sleep(104)
    if len(sys.argv)>1:
        if sys.argv[1]=="cron":
            print("CRON")
            cron=True
    boot_json=boot()
    try:
        main(boot_json)
    except KeyboardInterrupt:
        with open("boot.json","r") as f:
            boot_json=json.load(f)
        boot_json["started"]=False
        with open("boot.json","w") as wf:
            json.dump(boot_json, wf, sort_keys=False,indent='\t', separators=(',', ': '))
    except Exception as e:
        logger.exception("main func exception"+str(e))
        with open("boot.json","r") as f:
            boot_json=json.load(f)
        boot_json["started"]=False
        with open("boot.json","w") as wf:
            json.dump(boot_json, wf, sort_keys=False,indent='\t', separators=(',', ': '))
