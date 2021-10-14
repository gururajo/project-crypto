from binance.spot import Spot
import json,time
import logging,sys
import logging.config

logging.config.fileConfig('log_config.conf')
logger = logging.getLogger("MARKET")

def buy(symbol,price,type_o="LIMIT",timeInforce="GTC"):
    with open("keys.json","r") as f:
        keys=json.load(f)
    with open("orders.json","r") as f:
        orders=json.load(f)
    logger.info("Got BUY req: "+str(symbol)+" p:"+str(price))
    client= Spot(base_url='https://testnet.binance.vision',key=keys["api_key"], secret=keys["secret_key"])
    wallet=client.account()
    with open("wallet.json","w") as wf:
        json.dump(wallet,wf, sort_keys=False,indent='\t', separators=(',', ': '))
    # get quantity by checking balance
    # need to add sell function
    # another parallel script to sell filled orders
    # get last 1day to create report in seconds
    order=client.new_order(symbol=symbol,side="BUY",type=type_o,timeInForce=timeInforce,quantity=quantity,price=price)
    time.sleep(1)
    orders.append(order)
    o_orders=client.get_open_orders()
    with open("open_orders.json","w") as wf:
        json.dump(o_orders, wf, sort_keys=False,indent='\t', separators=(',', ': '))
    with open("orders.json","w") as wf:
        json.dump(orders, wf, sort_keys=False,indent='\t', separators=(',', ': '))

    # client.get_order("BTCUSDT", orderId =5522552)

    # client.get_order("BTCUSDT", orderId =5522552)

# buy(symbol="TRXUSDT",quantity=200,price=0.0965)