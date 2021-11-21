import re,os,json

def cleanup_orders_json():
    with open("orders.json","r") as f :
        orders=json.load(f)
    updated_orders=[]
    for order in orders:
        if order["side"]!="SELL":
            updated_orders.append(order)
    with open("orders.json","w") as wf :
        orders=json.dump(updated_orders,wf, sort_keys=False,indent='\t', separators=(',', ': '))


def cleanup_sell_orders_json():
    with open("sell_orders.json","r") as f :
        orders=json.load(f)
    updated_orders={}
    for order in orders:
        if orders[order]["status"]!="FILLED" and orders[order]["status"]!="CANCELED":
            updated_orders[order]=orders[order]
    with open("sell_orders.json","w") as wf :
        orders=json.dump(updated_orders,wf, sort_keys=False,indent='\t', separators=(',', ': '))

def cleanup_sp_out_log():
    for file in os.listdir("."):
        if file.startswith("sp_out") and file != "sp_out.log":
            os.remove(file)
    with open("sp_out.log","w") as wf:
        wf.write("")

def cleanup_reports_json():
    for file in os.listdir("reports/"):
        if file.endswith(".json"):
            os.remove(os.path.join("reports",file))


def main():
     cleanup_orders_json()
     cleanup_sell_orders_json()
     cleanup_sp_out_log()
     cleanup_reports_json()


if __name__== "__main__":
    main()