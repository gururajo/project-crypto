from binance.spot import Spot
import json,time
import logging,sys
import logging.config

logging.config.fileConfig('log_config.conf')
logger = logging.getLogger("MARKET")

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
    if balance > 11:
        quantity=11/price
        logger.info("Buying "+str(symbol)+" Q:"+str(quantity)+" P:"+str(price))
        order=client.new_order(symbol=symbol,side="BUY",type=type_o,timeInForce=timeInforce,quantity=quantity,price=price)
        time.sleep(1)
    else:
        logger.info("Not enough Balance to buy "+str(symbol)+" P:"+str(price))
        return None

    with open("orders.json","r") as f:
        orders=json.load(f)
    orders.append(order)
    o_orders=client.get_open_orders()
    with open("open_orders.json","w") as wf:
        json.dump(o_orders, wf, sort_keys=False,indent='\t', separators=(',', ': '))
    with open("orders.json","w") as wf:
        json.dump(orders, wf, sort_keys=False,indent='\t', separators=(',', ': '))
    return order

    # client.get_order("BTCUSDT", orderId =5522552)

    # client.get_order("BTCUSDT", orderId =5522552)

# buy(symbol="TRXUSDT",quantity=200,price=0.0965)