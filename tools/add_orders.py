import json,os,sys
from binance.spot import Spot

with open("keys.json","r") as f:
    keys=json.load(f)
print("Starting the seller_stoploss")
client= Spot(key=keys["api_key"], secret=keys["secret_key"])

try:
    o_orders=client.get_open_orders()
except Exception as e:
    print("error when getting get_open_orders()")
orders_list=[]
i=0
with open("sell_orders.json","r") as f:
    s_orders=json.load(f)
for order in o_orders:
    symbol=order["symbol"]
    id=order["orderId"]
    orders_list.append(id)
    side=order["side"]
    price=order["price"]
    already_present="\tnot present"
    for o in s_orders:
        if s_orders[o]["orderId"]==id:
            already_present="\tyes"
    print(i,symbol,price,side,id, already_present)
    i+=1
id_r=int(input())
print(orders_list[id_r])
print(o_orders[id_r])
if orders_list[id_r]!=o_orders[id_r]["orderId"]:
    print("Some error please debug")
    sys.exit()

with open("sell_orders.json","r") as f:
    s_orders=json.load(f)
s_orders[o_orders[id_r]["orderId"]]=o_orders[id_r]
with open("sell_orders.json","w")as wf :
    json.dump(s_orders,wf, sort_keys=False,indent='\t', separators=(',', ': '))