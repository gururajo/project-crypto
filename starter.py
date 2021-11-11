import os,json

with open("boot.json","r") as f:
    boot_json=json.load(f)
boot_json["started"]=False
boot_json["started_1hr"]=False
boot_json["started_4hr"]=False
boot_json["started_1d"]=False
boot_json["seller_started"]=False
boot_json["seller_stoploss_started"]=False
with open("boot.json","w") as wf:
    json.dump(boot_json, wf, sort_keys=False,indent='\t', separators=(',', ': '))
