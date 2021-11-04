import logging,sys
import logging.config
import json,re,time
from binance.spot import Spot

logging.config.fileConfig('log_config.conf')
logger = logging.getLogger("MARKET")
buy_price_thres=25

def get_corrected_price(symbol,price):
    global buy_price_thres

    with open("exchange.json","r") as f:
        exchanges=json.load(f)
        exchanges=exchanges["symbols"]
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
    quantity=buy_price_thres/price
    quantity=int(quantity/q_stepsize)/(1/q_stepsize)
    try:
        gap=re.search("\.0*1",str('{:.10f}'.format(tick_size))).group()
        print("got gap",gap)
        # print(str('{:.10f}'.format(price)))
        # print(re.search("\.[0-9]*",str('{:.10f}'.format(price))))
        gap2=re.search("\.[0-9]*",str('{:.10f}'.format(price))).group()
        # print("got gap2",gap2)
        if len(gap2) > len(gap):
            price=re.search("[0-9]*\.[0-9]{"+str(len(gap)-1)+"}",str('{:.10f}'.format(price))).group()
            # print(price)
    except Exception as e:
        print("ops1",e)
    try:
        gap=re.search("\.0*1",str('{:.10f}'.format(q_stepsize))).group()
        print("got gap")
        gap2=re.search("\.[0-9]*",str('{:.10f}'.format(quantity))).group()
        if len(gap2) > len(gap):
            quantity=re.search("[0-9]*\.[0-9]{"+str(len(gap)-1)+"}",str('{:.10f}'.format(quantity))).group()
    except Exception as e:
        print("ops2",e)

    print(price,quantity)
    print("total Amt",float(price)*float(quantity))
    return price,quantity

def get_order_det():
    with open("keys.json","r") as f:
        keys=json.load(f)
    logger.info("Starting the seller_stoploss")
    client= Spot(key=keys["api_key"], secret=keys["secret_key"])
    # print(client.account())
    success=False
    while not success:
        try:
            o_orders=client.time()
            print(o_orders)
            print(time.time())
            print(time.time()-(o_orders["serverTime"]/1000))
            success=True
        except Exception as e:
            if e.error_code == -2011:
                success=True
            else:
                logger.exception("error when cancelling order")
    print("Done")

def get_dynamic_price(client):
    # client=Spot()
    wallet=client.account()
    total=0.0
    for crypt in wallet["balances"]:
        if float(crypt["free"]) > 0.0 or float(crypt["locked"]) > 0.0:
            if crypt["asset"]!="USDT":
                symbol=crypt["asset"]+"USDT"
            else:
                total+=float(crypt["free"]) + float(crypt["locked"])
                continue
            # print(symbol)
            try:
                price=client.ticker_price(symbol)
                time.sleep(0.2)
            except Exception as e:
                logger.exception("error when fetching ticker price S:"+str(symbol))
                return 25
            price=float(price["price"])
            total+=(price*float(crypt["free"]))+(price*float(crypt["locked"]))
    price=int((total-10)/15)
    if price < 25:
        price =25

    return price


with open("keys.json","r") as f:
    keys=json.load(f)
logger.info("Starting the seller_stoploss")
client= Spot(key=keys["api_key"], secret=keys["secret_key"])
print(get_corrected_price("TRXUSDT",0.1012))
# print(get_corrected_price("BTCUSDT",60000.89))