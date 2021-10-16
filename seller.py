from os import truncate
from binance.spot import Spot
import json,time,re
import logging,sys
import trade
import logging.config


logging.config.fileConfig('log_config.conf')
logger = logging.getLogger("SELLER")

def get_per(principle,percentage):
    return principle * ((100 + percentage)/ 100)
def boot():
    with open("boot.json","r") as f:
        boot_json=json.load(f)
    if boot_json["seller_started"]:
        boot_json["seller_started"]=False
        with open("boot.json","w") as wf:
            json.dump(boot_json,wf, sort_keys=False,indent='\t', separators=(',', ': '))
        logger.info("Looks like seller is started, setting as false and waiting for 15 secs")
        time.sleep(15)
        with open("boot.json","r") as f:
            boot_json=json.load(f)
        if boot_json["seller_started"]:
            logger.info("seller present,  Bye!!")
            sys.exit()
        else:
            boot_json["seller_started"]=True
    else:
        boot_json["seller_started"]=True
    print(boot_json)
    return boot_json



boot_json= boot()
with open("keys.json","r") as f:
    keys=json.load(f)
logger.info("Starting the seller")
client= Spot(base_url='https://testnet.binance.vision',key=keys["api_key"], secret=keys["secret_key"])
time.sleep(1)
while True:
    with open("orders.json","r")as f :
        orders=json.load(f)
    created_order={}
    for order in orders:
        if order["status"]=="NEW" and order["side"]=="BUY":
            order_id=order["orderId"]
            symbol=order["symbol"]
            latest_order_det=client.get_order("TRXUSDT",orderId = order_id)
            if latest_order_det["status"]=="FILLED":
                price=get_per(order["price"],3.2)
                try:
                    order_ret=trade.sell(symbol=symbol,price=price)
                    created_order[order_id]=order

                except Exception as e:
                    logger.exception("Error in sell order: "+str(symbol)+" P:"+str(price))
                    continue
            elif latest_order_det["status"]=="CANCELED" or latest_order_det["status"]=="EXPIRED" or latest_order_det["status"]=="REJECTED":
                logger.info("ORder :"+str(order_id)+" is canceled n:"+str(symbol)+" S:"+str(latest_order_det["status"]))
                created_order[order_id]=latest_order_det
            else:
                logger.info("ORder :"+str(order_id)+" is still not filled n:"+str(symbol)+" S:"+str(latest_order_det["status"]))
    print(created_order.keys())
    with open("orders.json","r")as f :
        orders=list(json.load(f))

    temp_orders=[]
    for order in orders:
        if order["orderId"] not in list(created_order.keys()):
            temp_orders.append(order)

    orders=temp_orders
    with open("orders.json","w")as wf :
        json.dump(orders,wf, sort_keys=False,indent='\t', separators=(',', ': '))
    with open("sell_orders.json","r")as f :
        s_orders=json.load(f)
    for id in created_order:
        s_orders[id]=created_order[id]
    with open("sell_orders.json","w")as wf :
        json.dump(s_orders,wf, sort_keys=False,indent='\t', separators=(',', ': '))
    with open("boot.json","r") as f:
        boot_json=json.load(f)
    boot_json["seller_started"]=True
    with open("boot.json","w") as wf:
        json.dump(boot_json,wf, sort_keys=False,indent='\t', separators=(',', ': '))


    time.sleep(10)


