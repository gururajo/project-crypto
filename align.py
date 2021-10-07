import re,time
import json

def align_report(report):
    # print(report)
    # time.sleep(5)
    report=re.sub("\[\\n			","[ ",report)
    # print(report)
    # time.sleep(20)
    report=re.sub("\\n			"," ",report)
    report=re.sub("\\n		\]"," ]",report)
    return report




with open("reports/report_15s_October 07 19-22.json", "r") as f:
    diss_report=f.read()
diss_report= align_report(diss_report)
with open("reports/report_15s_October 07 19-22.json", "w") as wf:
    wf.write(diss_report)