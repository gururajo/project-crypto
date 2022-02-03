from binance.spot import Spot
import json,time,re,sys




def get_trades(client,days):
    print("f yea")
    # client=Spot()
    trades={}
    symbols=client.account()["balances"]
    time.sleep(.5)
    for symbol in symbols:
        sym=symbol["asset"]+"USDT"

        if (not (float(symbol["free"])>0 or float(symbol["locked"])>0)) or sym=="USDTUSDT":
            continue
        print("symbol",sym)
        if not sym.endswith("USDT") or sym.endswith("BULLUSDT") or sym.endswith("BEARUSDT"):
            continue
        trade=client.get_orders(sym)
        time.sleep(.5)

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
            buy_price=0
            buy_quant=0
            # print("As:",buy_price,buy_quant)

    # print(sym, /)
    return buy_price

def main():
    with open("../keys.json","r") as f:
        keys=json.load(f)
    client= Spot(key=keys["api_key"], secret=keys["secret_key"])
    try:
        prices=client.ticker_price()
        time.sleep(0.2)
    except Exception as e:
        print("error when fetching ticker prices")
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
        # if not trade == "PYRUSDT":
        #     continue
        ret=pnl_of_sym(trade,trades[trade],client.ticker_price)
        for price in prices:
            if price["symbol"]==trade:
                present_price=float(price["price"])
                break
        print(trade,"{:.5f}".format(ret),present_price,"\t",present_price-ret)
        # break

    with open(last_report,"w") as wf :
        json.dump(trades,wf, sort_keys=False,indent='\t', separators=(',', ': '))



if __name__== "__main__":
    main()
