from binance.spot import Spot
import json,time,re
import logging,sys
import logging.config

logging.config.fileConfig('log_config.conf')
logger = logging.getLogger("TRADE")
def get_corrected_price(symbol,price):
    with open("exchange.json","r") as f:
        exchanges=json.load(f)
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

    print(price,quantity)
    print("total Amt",price*quantity)
    return price,quantity


def buy(symbol,price,type_o="LIMIT",timeInforce="GTC"):
    with open("keys.json","r") as f:
        keys=json.load(f)

    logger.info("Got BUY req: "+str(symbol)+" p:"+str(price))
    client= Spot(base_url='https://testnet.binance.vision',key=keys["api_key"], secret=keys["secret_key"])
    time.sleep(1)
    wallet=client.account()
    with open("wallet.json","w") as wf:
        json.dump(wallet,wf, sort_keys=False,indent='\t', separators=(',', ': '))
    # get quantity by checking balance
    # need to add sell function
    # another parallel script to sell filled orders
    # get last 1day to create report in seconds
    # put 24hr high limit
    balance=wallet["balances"]
    for bal in balance:
        if bal["asset"]=="USDT":
            balance=float(bal["free"])
            break
    if balance > 12:
        ret=get_corrected_price(symbol,price)
        if ret:
            price,quantity=ret
        else:
            logger.error("Some error in get_corrected_prices")
            return

        logger.info("Buying "+str(symbol)+" Q:"+str(quantity)+" P:"+str(price))

        # client.new_order(symbol="",side="BUY",type="LIMIT",timeInForce="GTC",quantity=quantity,price=price)
        order=client.new_order(symbol=symbol,side="BUY",type=type_o,timeInForce=timeInforce,quantity=quantity,price=price)
        time.sleep(1)
    else:
        logger.info("Not enough Balance to buy "+str(symbol)+" P:"+str(price))
        return None

    with open("orders.json","r") as f:
        orders=json.load(f)
    orders.append(order)
    with open("orders.json","w") as wf:
        json.dump(orders, wf, sort_keys=False,indent='\t', separators=(',', ': '))
    o_orders=client.get_open_orders()
    with open("open_orders.json","w") as wf:
        json.dump(o_orders, wf, sort_keys=False,indent='\t', separators=(',', ': '))

    return order

    # client.get_order("BTCUSDT", orderId =5522552)

    # client.get_order("BTCUSDT", orderId =5522552)

def sell(symbol,price,type_o="LIMIT",timeInforce="GTC"):
    with open("keys.json","r") as f:
        keys=json.load(f)

    logger.info("Got SELL req: "+str(symbol)+" p:"+str(price))
    client= Spot(base_url='https://testnet.binance.vision',key=keys["api_key"], secret=keys["secret_key"])
    time.sleep(1)
    wallet=client.account()
    with open("wallet.json","w") as wf:
        json.dump(wallet,wf, sort_keys=False,indent='\t', separators=(',', ': '))
    # get quantity by checking balance
    # need to add sell function
    # another parallel script to sell filled orders
    # get last 1day to create report in seconds
    # put 24hr high limit
    balance=wallet["balances"]
    for bal in balance:
        if bal["asset"]==str(symbol).replace("USDT",""):
            quantity=float(bal["free"])
            break
    else:
        logger.error("Not find symbol in wallet:"+str(symbol))
        return

    if quantity > 0:
        ret=get_corrected_price(symbol,price)
        if ret:
            price,_=ret
        else:
            logger.error("Some error in get_corrected_prices")
            return

        logger.info("Selling "+str(symbol)+" Q:"+str(quantity)+" P:"+str(price))

        # client.new_order(symbol="",side="SELL",type="LIMIT",timeInForce="GTC",quantity=quantity,price=price)
        # quantity=200
        order=client.new_order(symbol=symbol,side="SELL",type=type_o,timeInForce=timeInforce,quantity=quantity,price=price)
        time.sleep(1)
    else:
        logger.info("Not enough Balance to sell "+str(symbol)+" P:"+str(price))
        return None

    with open("orders.json","r") as f:
        orders=json.load(f)
    orders.append(order)
    with open("orders.json","w") as wf:
        json.dump(orders, wf, sort_keys=False,indent='\t', separators=(',', ': '))
    o_orders=client.get_open_orders()
    with open("open_orders.json","w") as wf:
        json.dump(o_orders, wf, sort_keys=False,indent='\t', separators=(',', ': '))

    return order

if __name__=="__main__":
    # buy(symbol="TRXUSDT",quantity=200,price=0.0965)
    # # print(buy(symbol="TRXUSDT",price=0.1012))
    pass