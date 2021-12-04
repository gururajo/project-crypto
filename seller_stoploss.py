from os import truncate
from binance.spot import Spot
import json,time,re
import logging,sys
import trade
import logging.config


logging.config.fileConfig('log_config.conf')
logger = logging.getLogger("SELLER_stoploss")
min=10

def get_per(principle,percentage):
    return principle * ((100 + percentage)/ 100)

def get_per_change(first,last):

    if first==0:
        return last
    diff=last-first
    per=(diff/first)*100
    return per

def cancel_n_place_new(client,new_b_id,bought_orders_with_old,s_orders):
    # pass
    # client=Spot()
    logger.info("new low price cause Order completed, cancelling old ones and creating new sell order")
    old_b_id=None
    for o_id in bought_orders_with_old:
        if bought_orders_with_old[o_id] == new_b_id:
            old_b_id=o_id
            break
    if old_b_id ==None:
        logger.error("couldn't find the old_b_id in the bought orders_with old OB:"+str(old_b_id)+" ")
        return None
    logger.info("Got old buy and new buy order ids OB:"+str(old_b_id)+" NB"+str(new_b_id))
    symbol=s_orders[new_b_id]["symbol"]
    new_sell_id=s_orders[new_b_id]["orderId"]
    old_sell_id=s_orders[old_b_id]["orderId"]

    old_sell_price=float(s_orders[old_b_id]["price"])
    new_sell_price=float(s_orders[new_b_id]["price"])

    old_sell_quant=float(s_orders[old_b_id]["origQty"])
    new_sell_quant=float(s_orders[new_b_id]["origQty"])

    cal_new_sell_price=((old_sell_price*old_sell_quant)+(new_sell_price*new_sell_quant))/(old_sell_quant+new_sell_quant)
    logger.info("Cancelling sell orders OS:"+str(old_sell_id)+" NS"+str(new_sell_id))


    try:
        client.cancel_order(symbol,orderId=new_sell_id)

    except Exception as e:
        if e.error_code == -2011:
            logger.info("Looks like already cancelled"+str(new_sell_id))
            cal_new_sell_price=old_sell_price

        else:
            logger.exception("error when cancelling order")
            return None
    logger.info("Successfully cancelled new sell order")
    time.sleep(1)

    try:
        client.cancel_order(symbol,orderId=old_sell_id)

    except Exception as e:
        if e.error_code == -2011:
            logger.info("Looks like already cancelled"+str(old_sell_id))

        else:
            logger.exception("error when cancelling order")
            return None
    logger.info("Successfully cancelled old sell order")
    time.sleep(1)


    try:
        new_sell_order=trade.sell(symbol=symbol,price=get_per(cal_new_sell_price,.2))
        if new_sell_order==None:
            logger.error("Error occured when selling combined order trade.sell returnde none")
            return None
    except Exception as e:
        logger.exception("Error occured when selling combined order")
        return None
    new_sell_order={new_b_id:new_sell_order}
    return old_b_id,new_b_id,new_sell_order

def check_if_neg_trig_is_true(symbol):
    with open("boot.json","r") as f:
        boot_json=json.load(f)
    diff=boot_json["last_report"]
    with open(diff,"r") as f:
        diff=json.load(f)
    if diff[symbol]["neg_trig"][1]:
        return True
    else:
        return False



def boot():
    with open("boot.json","r") as f:
        boot_json=json.load(f)
    if boot_json["seller_stoploss_started"]:
        boot_json["seller_stoploss_started"]=False
        with open("boot.json","w") as wf:
            json.dump(boot_json,wf, sort_keys=False,indent='\t', separators=(',', ': '))
        logger.info("Looks like seller_stoploss is started, setting as false and waiting for 12 mins")
        time.sleep(15*60)
        with open("boot.json","r") as f:
            boot_json=json.load(f)
        if boot_json["seller_stoploss_started"]:
            logger.info("seller_stoploss present,  Bye!!")
            sys.exit()
        else:
            boot_json["seller_stoploss_started"]=True
    else:
        boot_json["seller_stoploss_started"]=True
    print(boot_json)
    return boot_json

def get_slots(client,symb):
    try:
        orders=client.get_orders(symb)
        # print(orders)
    except Exception:
        logger.exception("Exceptio when getting trades for stoploss")
        return None
    slots=0
    quantity=0
    for order in orders:
        if order["side"]=="BUY" and float(order["executedQty"])>0:
            slots+=1
            quantity+=float(order["executedQty"])
        if order["side"]=="SELL" and float(order["executedQty"])>0:
            if float(order["executedQty"])==quantity:
                slots=0
                quantity=0
            else:
                slots-=1
                quantity-=float(order["executedQty"])
        if quantity<0:
            slots=0
            quantity=0
    logger.info("Slots: "+str(slots)+" S:"+str(symb))
    return slots

def main():
    global min
    boot_json=boot()
    #
    #
    # chage key file name
    with open("keys.json","r") as f:
        keys=json.load(f)
    logger.info("Starting the seller_stoploss")
    client= Spot(key=keys["api_key"], secret=keys["secret_key"])
    bought_orders=[]
    bought_orders_with_old={}
    added_orders={}

    while True:
        time.sleep(min*60)
        updated_orders={}
        try:
            o_orders=client.get_open_orders()
            with open("open_orders.json","w") as wf:
                json.dump(o_orders, wf, sort_keys=False,indent='\t', separators=(',', ': '))
        except Exception as e:
            logger.exception("error when getting get_open_orders()")

        with open("bought_orders.json","r") as f:
            uo=json.load(f)
        bought_orders=uo["bought_orders"]
        bought_orders_with_old=uo['bought_orders_with_old']
        with open("sell_orders.json","r") as f:
            s_orders=json.load(f)

        for b_order_id in s_orders:
            if s_orders[b_order_id]["side"]=="SELL":
                if s_orders[b_order_id]["status"] == "NEW" or s_orders[b_order_id]["status"] == "PARTIALLY_FILLED":
                    symbol=s_orders[b_order_id]["symbol"]
                    sell_orderid=s_orders[b_order_id]["orderId"]
                    old_price=float(s_orders[b_order_id]["price"])
                    #update this Olay, you have to remove the old sell order-Done
                    if b_order_id in bought_orders:
                        try:
                            ret =cancel_n_place_new(client,b_order_id,bought_orders_with_old,s_orders)
                            if ret != None:
                                old_b_id,new_b_id,new_sell_order=ret
                            else:
                                logger.error("cancel_n_place_new returned None")
                                continue
                        except Exception as e:
                            logger.exception("Error occured in cancel_n_place_new")
                            continue
                        logger.info("Completed selling new combined order")

                        added_orders[new_b_id]=new_sell_order[new_b_id]
                        bought_orders.remove(b_order_id)
                        bought_orders_with_old.pop(old_b_id)
                        continue

                    try:
                        new_order_det=client.get_order(symbol,orderId=sell_orderid)
                        time.sleep(.5)
                    except Exception as e:
                        logger.exception("error when fetching sell order details S:"+str(symbol))
                        continue
                    if new_order_det["status"]== "FILLED" or new_order_det["status"]== "CANCELED" or new_order_det["status"]== "PENDING_CANCEL" or new_order_det["status"]== "REJECTED" or new_order_det["status"]== "EXPIRED":
                        updated_orders[b_order_id]=new_order_det
                        continue
                    elif new_order_det["status"]== "NEW" :
                        #understand this , osmthing wrong
                        if b_order_id in list(bought_orders_with_old.keys()):
                            logger.info("already bought cause of low price")
                            continue
                        try:
                            price=client.ticker_price(symbol)
                        except Exception as e:
                            logger.exception("error when fetching ticker price S:"+str(symbol))
                            continue
                        new_price=float(price["price"])
                        if get_per_change(old_price,new_price) < -25:
                            if get_per_change(old_price,new_price) > -25 -((get_slots(client,symbol)-1)*7):
                                continue
                            logger.info("price dropped "+str(-25 -((get_slots(client,symbol)-1)*7))+", so buying again to reduce avg bought price")
                            if check_if_neg_trig_is_true(symbol):
                                logger.info("not a good time to buy, neg_trig is true: "+str(symbol))
                                continue
                            try:
                                order=trade.buy(symbol,price=get_per(new_price,-0.2),force=True)
                                if order == None:
                                    logger.error("exception occured when placing buy order S:"+str(symbol))
                                    continue
                            except Exception as e:
                                logger.exception("exception occured when placing buy order S:"+str(symbol))
                                continue
                            bought_order_id=order["orderId"]
                            bought_orders.append(str(bought_order_id))
                            bought_orders_with_old[str(b_order_id)]=str(bought_order_id)
                            logger.info("Bought "+str(symbol)+" again")
                            continue
                    else: continue
                else:
                    continue
            elif s_orders[b_order_id]["side"]=="BUY":
                if b_order_id in bought_orders:
                    logger.error("For some reason this order cancelled,")
                    # logger.info("For some reason this order cancelled, trying again since its crucial")
                    logger.info("S:"+str(s_orders[b_order_id]["symbol"])+" P:"+s_orders[b_order_id]["price"])
                    bought_orders.remove(b_order_id)
                    for o_id in bought_orders_with_old:
                        if bought_orders_with_old[o_id]==b_order_id:
                            bought_orders_with_old.pop(o_id)
                            break
                    continue

        if len(list(bought_orders_with_old.keys()))>0 or len(list(updated_orders.keys()))>0:
            logger.info("OBERALL bought orders:"+str(bought_orders_with_old)+" Updated orders: "+str(list(updated_orders.keys())))
        if len(list(bought_orders_with_old.keys()))>0:
            min=1
        if len(list(bought_orders_with_old.keys()))==0:
            min=10
        with open("sell_orders.json","r") as f:
            s_orders=json.load(f)
        to_write={}
        for b_id in s_orders:
            try:
                to_write[b_id]=updated_orders[b_id]
                logger.info('updatedorder'+str(b_id))
            except KeyError:
                to_write[b_id]=s_orders[b_id]
                # logger.info('Keyyerror:'+str(b_id))
        for b_id in added_orders:
            to_write[b_id]=added_orders[b_id]
        with open("sell_orders.json","w")as wf :
            json.dump(to_write,wf, sort_keys=False,indent='\t', separators=(',', ': '))
        with open("boot.json","r") as f:
            boot_json=json.load(f)
        boot_json["seller_stoploss_started"]=True
        with open("boot.json","w") as wf:
            json.dump(boot_json,wf, sort_keys=False,indent='\t', separators=(',', ': '))

        with open("bought_orders.json","w") as wf:
            json.dump({"bought_orders_with_old":bought_orders_with_old,"bought_orders":bought_orders},wf, sort_keys=False,indent='\t', separators=(',', ': '))



if __name__== "__main__":
    try:
        main()
    except KeyboardInterrupt:
        with open("boot.json","r") as f:
            boot_json=json.load(f)
        boot_json["seller_stoploss_started"]=False
        with open("boot.json","w") as wf:
            json.dump(boot_json,wf, sort_keys=False,indent='\t', separators=(',', ': '))
    except Exception as e:
        logger.exception("exception in main func"+str(e))
        with open("boot.json","r") as f:
            boot_json=json.load(f)
        boot_json["seller_stoploss_started"]=False
        with open("boot.json","w") as wf:
            json.dump(boot_json,wf, sort_keys=False,indent='\t', separators=(',', ': '))
















