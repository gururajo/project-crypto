import re,os,json,sys
import time
path="."

def cleanup_orders_json():
    global path
    with open(os.path.join(path,"orders.json"),"r") as f :
        orders=json.load(f)
    updated_orders=[]
    for order in orders:
        if order["side"]!="SELL":
            updated_orders.append(order)
    with open(os.path.join(path,"orders.json"),"w") as wf :
        orders=json.dump(updated_orders,wf, sort_keys=False,indent='\t', separators=(',', ': '))


def cleanup_sell_orders_json():
    global path
    with open(os.path.join(path,"sell_orders.json"),"r") as f :
        orders=json.load(f)
    updated_orders={}
    for order in orders:
        if orders[order]["status"]!="FILLED" and orders[order]["status"]!="CANCELED":
            updated_orders[order]=orders[order]
    with open(os.path.join(path,"sell_orders.json"),"w") as wf :
        orders=json.dump(updated_orders,wf, sort_keys=False,indent='\t', separators=(',', ': '))

def cleanup_sp_out_log():
    overall_log=""
    global path
    for file in os.listdir(path):
        if file.startswith("sp_out") and file != "sp_out.log":
            with open(os.path.join(path,file),"r")as f:
                overall_log+=str(f.read())
            os.remove(file)
    with open(os.path.join(path,"sp_out.log"),"r") as wf:
        overall_log+=str(wf.read())
    with open(os.path.join(path,"sp_out.log"),"w") as wf:
        wf.write("new report started\n")
    try:
        os.makedirs("monthly_logs")
    except FileExistsError:
        pass
    with open(os.path.join(path,"monthly_logs",time.strftime("monthly_log_%B.log")),"a") as wf:
        wf.write(overall_log)

def cleanup_reports_json():
    for file in os.listdir(os.path.join(path,"reports/")):
        if file.endswith(".json"):
            os.remove(os.path.join(path,"reports",file))


def main():
    global path
    if len(sys.argv)>1:
        path=sys.argv[1]

    cleanup_orders_json()
    cleanup_sell_orders_json()
    cleanup_sp_out_log()
    cleanup_reports_json()



if __name__== "__main__":
    main()