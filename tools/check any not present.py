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

try:
    wallet=client.account()
except Exception as e:
    print("error when getting account info"+ str(e))
    sys.exit()
with open("wallet.json","w") as wf:
    json.dump(wallet,wf, sort_keys=False,indent='\t', separators=(',', ': '))

for bal in wallet["balances"]:
    if float(bal["free"] ) >0 or float(bal["locked"])>0:
        for o in o_orders:
            # print(o["symbol"].lower(),bal["asset"]+"USDT".lower())
            if o["symbol"].lower()==bal["asset"].lower()+"USDT".lower():
                bal_c=float(bal["free"] )+float(bal["locked"])
                if float(o["origQty"])<bal_c or float(o["origQty"])>bal_c:
                    print("quantity not all, please check",bal["asset"])
                break
        else:
            print("no order for ",bal["asset"])