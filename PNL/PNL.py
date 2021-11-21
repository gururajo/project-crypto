from binance.spot import Spot
import json,time,re,sys



def get_trades(client,days):
    print("f yea")
    # client=Spot()
    trades={}
    symbols=client.exchange_info()["symbols"]
    time.sleep(.5)
    for symbol in symbols:
        sym=symbol["symbol"]
        if not sym.endswith("USDT") or sym.endswith("BULLUSDT") or sym.endswith("BEARUSDT"):
            continue
        trade=client.get_orders(sym,startTime=str(int((time.time()- (days*86400))*1000)))
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
        if trade["status"]=="FILLED" and trade["side"]=="SELL" and buy_quant>=float(trade["executedQty"]):
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

    days=30
    try:
        if sys.argv[1].isnumeric():
            days=int(sys.argv[1])
            print(days)
    except IndexError:
        days=30
    last_report="trades_"+str(time.strftime("%d-%m-%Y_"+str(days)+".json"))
    # -f : Fresh
    if "-f" in sys.argv:
        print("-f")
        trades=get_trades(client,days)
    else:
        try:
            with open(last_report,"r") as f:
                trades=json.load(f)
        except FileNotFoundError:
            trades=get_trades(client,days)

    pnl=0
    upnl=0
    for trade in trades:
        # if not trade == "BADGERUSDT":
        #     continue
        ret=pnl_of_sym(trade,trades[trade],client.ticker_price)
        pnl+=ret[0]
        upnl+=ret[1]
        print(trade,ret[0]," "*10,ret[1])
        # break

    with open(last_report,"w") as wf :
        json.dump(trades,wf, sort_keys=False,indent='\t', separators=(',', ': '))

    print("realized PNL: ",pnl,"$ ",pnl*75,"Rs",sep="")
    print("unrealized PNL: ",upnl,"$ ",upnl*75,"Rs",sep="")
    print("overall PNL: ",pnl+upnl,"$ ",(pnl+upnl)*75,"Rs",sep="")

    with open("PNLs.json","r") as f:
        past_pnls=json.load(f)
    past_pnls[last_report]={
        "Realized":[str(pnl)+"$",str(pnl*75)+"₹"],
        "UnRealized":[str(upnl)+"$",str(upnl*75)+"₹"],
        "OverAll":[str(pnl+upnl)+"$",str((pnl+upnl)*75)+"₹"]
    }
    with open("PNLs.json","w") as wf:
        json.dump(past_pnls,wf, sort_keys=False,indent='\t', separators=(',', ': '))

if __name__== "__main__":
    main()
