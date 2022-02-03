import logging,sys, requests
from os import replace
import logging.config
import json,re,time
from binance.spot import Spot

with open("keys.json","r") as f:
    keys=json.load(f)
client= Spot(key=keys["api_key"], secret=keys["secret_key"])
print("calculating")
try:
    o_orders=client.get_open_orders()
except Exception as e:
    print("error when getting get_open_orders()")
try:
    prices=client.ticker_price()
    time.sleep(0.2)
except Exception as e:
    print("error when fetching ticker prices")
total_worth=0
total_present=0
for order in o_orders:
    # print(order)
    total_worth+=float(order["price"])*float(order["origQty"])
    symbol=order["symbol"]
    for price in prices:
        if price["symbol"]==symbol:
            present_price=float(price["price"])
            break
    total_present+=present_price*float(order["origQty"])
    print(order["symbol"],float(order["price"])*float(order["origQty"]),present_price*float(order["origQty"]))
usdt=0
for bal in client.account()["balances"]:

    if bal["asset"]=="USDT":
        usdt+=float(bal["free"]) + float(bal["locked"])
    if bal["asset"]=="BNB":
        symbol="BNBUSDT"
        for price in prices:
            if price["symbol"]==symbol:
                present_price=float(price["price"])
                break

        usdt+=(float(bal["free"]) + float(bal["locked"]))*present_price
print(total_worth+usdt,"$"," ",total_present+usdt,"$",sep="")