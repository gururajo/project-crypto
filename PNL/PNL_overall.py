from binance.spot import Spot
import json,time,re



def get_trades(client):
    print("f yea")
    # client=Spot()
    trades={}
    symbols=client.exchange_info()["symbols"]
    time.sleep(.5)
    for symbol in symbols:
        sym=symbol["symbol"]
        if not sym.endswith("USDT") or sym.endswith("BULLUSDT") or sym.endswith("BEARUSDT"):
            continue
        trade=client.get_orders(sym)
        time.sleep(.5)
        print(sym)
        if trade:
            trades[sym]=trade
    return trades

        # break
def pnl_of_sym(sym,trades,ticker_price):
    pnl=0
    upnl=0
    buy_quant=0.0
    buy_price=0.0
    for trade in trades:
        if trade["status"]=="FILLED" and trade["side"]=="BUY":
            # print("Bb:",buy_price,buy_quant)
            buy_price=((buy_price*buy_quant)+(float(trade["price"])*float(trade["executedQty"])))/(buy_quant+float(trade["executedQty"]))
            buy_quant+=float(trade["executedQty"])
            # print("Ab:",buy_price,buy_quant)
        if trade["status"]=="FILLED" and trade["side"]=="SELL":
            # print("Bs:",buy_price,buy_quant)
            pnl+=(float(trade["price"])*float(trade["executedQty"]))-(buy_price*float(trade["executedQty"]))
            buy_quant-=float(trade["executedQty"])
            # print("As:",buy_price,buy_quant)
    if buy_quant>0:
        upnl=(float(ticker_price(sym)["price"])*buy_quant)-(buy_quant*buy_price)
        time.sleep(0.2)
    return pnl,upnl

def main():
    with open("../keys.json","r") as f:
        keys=json.load(f)
    client= Spot(key=keys["api_key"], secret=keys["secret_key"])
    last_report="trades_"+str(time.strftime("%m-%Y.json"))
    try:
        with open(last_report,"r") as f:
            trades=json.load(f)
    except FileNotFoundError:
        trades=get_trades(client)
    pnl=0
    upnl=0
    for trade in trades:
        # if not trade == "CHESSUSDT":
        #     continue
        ret=pnl_of_sym(trade,trades[trade],client.ticker_price)
        pnl+=ret[0]
        upnl+=ret[1]
        print(trade,ret[0]," "*10,ret[1])
        # break

    with open(last_report,"w") as wf :
        orders=json.dump(trades,wf, sort_keys=False,indent='\t', separators=(',', ': '))

    print("realized PNL: ",pnl,"$ ",pnl*78,"Rs",sep="")
    print("unrealized PNL: ",upnl,"$ ",upnl*78,"Rs",sep="")
    print("overall PNL: ",pnl+upnl,"$ ",(pnl+upnl)*78,"Rs",sep="")

if __name__== "__main__":
    main()
