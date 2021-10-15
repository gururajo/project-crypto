import logging,sys
import logging.config
import json,re

logging.config.fileConfig('log_config.conf')
logger = logging.getLogger("MARKET")

def get_corrected_price(symbol,price):
    with open("exchange.json","r") as f:
        exchanges=json.load(f)["symbols"]
    tick_size=None
    q_stepsize=None
    for cryp in exchanges:
        if cryp["symbol"]!=symbol:
            continue
        filters=cryp["filters"]
        for filter in filters:
            if filter["filterType"]=="PRICE_FILTER":
                tick_size=float(filter["tickSize"])

            if filter["filterType"]=="LOT_SIZE":
                q_stepsize=float(filter["stepSize"])

        break
    else:
        logger.error("Couldn't fint the tickerSize in exchanges:"+str(symbol))
        return 0
    if tick_size==None or q_stepsize==None:
        logger.error("Couldn't fint the tickerSize or q_step in exchanges:"+str(symbol))
        return 0
    print("T ",tick_size)
    print("Q:" , q_stepsize)
    price=int(price/tick_size)/(1/tick_size)
    quantity=12.0/price
    quantity=int(quantity/q_stepsize)/(1/q_stepsize)
    try:
        gap=re.search("\.0*1",str('{:.10f}'.format(tick_size))).group()
        print("got gap")
        gap2=re.search("\.[0-9]*",str(price)).group()
        if len(gap2) > len(gap):
            price=float(re.search("[0-9]*\.[0-9]{"+str(len(gap)-1)+"}",str(price)).group())
    except Exception as e:
        print("ops",e)


    print("total Amt",price*quantity)
    return price,quantity
print(get_corrected_price("TRXUSDT",0.1012))