from binance.spot import Spot
import json,time

def buy(symbol,quantity,price,type_o="LIMIT",timeInforce="GTC"):
    with open("keys.json","r") as f:
        keys=json.load(f)


    client= Spot(base_url='https://testnet.binance.vision',key=keys["api_key"], secret=keys["secret_key"])
    wallet=client.account()
    with open("wallet.json","w") as wf:
        json.dump(wallet,wf, sort_keys=False,indent='\t', separators=(',', ': '))

    order=client.new_order(symbol=symbol,side="BUY",type=type_o,timeInForce=timeInforce,quantity=quantity,price=price)
    time.sleep()

    orders=client.get_open_orders()
    with open("orders.json","w") as wf:
        json.dump(orders, wf, sort_keys=False,indent='\t', separators=(',', ': '))

    # client.get_order("BTCUSDT", orderId =5522552)

buy(symbol="TRXUSDT",quantity=200,price=0.0965)