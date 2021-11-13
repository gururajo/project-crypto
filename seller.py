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
        time.sleep(2*60)
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

def get_per_change(first,last):

    if first==0:
        return last
    diff=last-first
    per=(diff/first)*100
    return per


def check_if_price_increased(order,client):
    symbol=order["symbol"]
    bought_price=float(order["price"])
    order_id=order['orderId']
    try:
        price=client.ticker_price(symbol)
    except Exception as e:
        logger.exception("error when fetching ticker price S:"+str(symbol))
        return None
    new_price=float(price["price"])
    if get_per_change(bought_price,new_price) > 2:
        return True
    else:
        return False


def main():
    boot_json= boot()
    with open("keys.json","r") as f:
        keys=json.load(f)
    logger.info("Starting the seller")
    client= Spot(key=keys["api_key"], secret=keys["secret_key"])
    time.sleep(1)
    while True:
        with open("orders.json","r")as f :
            orders=json.load(f)
        created_order={}
        for order in orders:
            if (order["status"]=="NEW" or order["status"]=="FILLED")  and order["side"]=="BUY":
                order_id=order["orderId"]
                logger.info("orderid:"+str(order_id))
                symbol=order["symbol"]
                try:
                    latest_order_det=client.get_order(symbol=symbol,orderId = order_id)
                except Exception as e:
                    logger.exception("error when getting order details")
                    time.sleep(30)
                    continue

                if latest_order_det["status"]=="FILLED":
                    price=get_per(float(order["price"]),3.2)
                    try:
                        order_ret=trade.sell(symbol=symbol,price=price)
                        if order_ret:
                            created_order[order_id]=order_ret
                        else:
                            logger.info("trade.sell return None :(")
                            continue
                    except Exception as e:
                        logger.exception("Error in sell order: "+str(symbol)+" P:"+str(price))
                        continue
                elif latest_order_det["status"]=="CANCELED" or latest_order_det["status"]=="EXPIRED" or latest_order_det["status"]=="REJECTED":
                    logger.info("ORder :"+str(order_id)+" is canceled n:"+str(symbol)+" S:"+str(latest_order_det["status"]))
                    created_order[order_id]=latest_order_det
                else:
                    logger.info("ORder :"+str(order_id)+" is still not filled n:"+str(symbol)+" S:"+str(latest_order_det["status"]))
                    # logger.info("checking if price is increased")
                    ret=check_if_price_increased(order,client)
                    if ret==None:
                        logger.error("check_if_price_increased returned None")
                        continue
                    if ret:
                        logger.error("price is greter than 2% of buy order, cancelling the order")
                        try:
                            client.cancel_order(symbol,orderId=order_id)
                        except Exception as e:
                            logger.exception("error when cancelling order")
                            continue
        print(created_order.keys())
        with open("boot.json","r") as f:
            boot_json=json.load(f)
        boot_json["seller_started"]=True
        with open("boot.json","w") as wf:
            json.dump(boot_json,wf, sort_keys=False,indent='\t', separators=(',', ': '))

        if len(list(created_order.keys()))>0:
            logger.info("created sellorder for :"+str(list(created_order.keys())))
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



        time.sleep(60)



if __name__== "__main__":
    try:
        main()
    except KeyboardInterrupt:
        with open("boot.json","r") as f:
            boot_json=json.load(f)
        boot_json["seller_started"]=False
        with open("boot.json","w") as wf:
            json.dump(boot_json,wf, sort_keys=False,indent='\t', separators=(',', ': '))
    except Exception as e:
        logger.exception("exception in main func"+str(e))
        with open("boot.json","r") as f:
            boot_json=json.load(f)
        boot_json["seller_started"]=False
        with open("boot.json","w") as wf:
            json.dump(boot_json,wf, sort_keys=False,indent='\t', separators=(',', ': '))



