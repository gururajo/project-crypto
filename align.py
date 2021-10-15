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




with open("reports/report_15m_October 15 15-23.json", "r") as f:
    diss_report=f.read()
diss_report= align_report(diss_report)
with open("reports/report_15m_October 15 15-23.json", "w") as wf:
    wf.write(diss_report)