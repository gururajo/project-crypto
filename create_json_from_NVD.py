##search_CVE_from_cpes_n_add_to_scripts.py

#!/usr/bin/python

###############################################################################
#
# Authors:
# Gururaj Otageri <gururaj@secpod.com>
#
# Date: 15/01/2021
#
# Version 1.0 - Requirement python >3.x
#
# Copyright:
# Copyright (C) 2021 SecPod , http://www.secpod.com
#
###############################################################################


import sys
import os, re, glob
import os.path
import logging
import logging.config
import requests
import json
import time


logging.config.fileConfig('sp_Logger.conf')
logger = logging.getLogger("CVEADDING")
if len(sys.argv)>1:
    print(sys.argv)
    if sys.argv[1]=="-debug":
        print("debug")
        logger.setLevel(10)
    else:
        print("Wrong argument")
        sys.exit()
else:
    
    logger.setLevel(20)
    print("fast")


# Check for proper required python version
req_version = (3, 0)
cur_version = sys.version_info
if cur_version < req_version:
    logger.error("[-] Python 3.x is required to run this framework...")
    sys.exit()

def get_cpe3_from_nse_data(nmap_nse_data):
    reliable = "yes"
    cpe3 = ""
    actual_cpe3 = ""

    ##Get cpe3 from nse file:
    cpe_string = re.findall('cpe3 = "(cpe.*?)"', nmap_nse_data)
    if(not cpe_string):
        return False, None, reliable, actual_cpe3

    else:
        if( not(cpe_string[0].endswith(':'))):
            cpe_string[0] = cpe_string[0] + ":"
        else:
            cpe_string[0] = cpe_string[0]

    ##Required to do magic later
    actual_cpe3 = cpe_string[0]

    if(cpe_string[0]):
        ## Covert cpe:2.3:a:advantech:webaccess\\/scada: --> cpe:2.3:a:advantech:webaccess%5C%2Fscada:
        cpe_string[0] = re.sub("\\\\\\\\/","%5C%2F", cpe_string[0])

    if(cpe_string[0] and cpe_string[0].endswith('_:')):
        ## Convert cpe:2.3:a:al-enterprise:omnivista_:  --> cpe:2.3:a:al-enterprise:omnivista_*
        cpe_string[0] = re.sub("_:", "_*", cpe_string[0])
        ## As cpe is not complete from NSE probably runtime model needs to be appended
        reliable = "no"

    if(cpe_string[0] and cpe_string[0].endswith('-:')):
        ## Convert cpe:2.3:h:asus:dsl-:  --> cpe:2.3:h:asus:dsl-*
        cpe_string[0] = re.sub("-:", "-*", cpe_string[0])
        ## As cpe is not complete from NSE probably runtime model needs to be appended
        reliable = "no"

    if(cpe_string[0] and cpe_string[0].endswith("\\!:")):
        ## Convert cpe:2.3:a:joomla:joomla\\!: --> cpe:2.3:a:joomla:joomla%5C!:
        cpe_string[0] = re.sub("\\\\\\\\!:","%5C!:", cpe_string[0])

    if(cpe_string[0] and re.findall(":\*:\*:.*:\*:", cpe_string[0])):
        cpe_string[0] = cpe_string[0][:-1]

    if(cpe_string[0]):
        cpe3 = cpe_string[0]


    ##Check cpe3 has both product part and vendor part; else return unreliable
    if(cpe3 and re.findall('cpe:2.3:o?a?h?:.*?:.*?:', cpe3)):
        reliable = "yes"
    elif(cpe3 and re.findall('cpe:2.3:o?a?h?:.*?:$', cpe3)):
        reliable = "no"

    if(cpe3):

        return True, cpe3, reliable, actual_cpe3
    else:
        return False, cpe3, reliable, actual_cpe3

def get_cpe_cve_map_form_nodes(cve_id,nodes,cpe_cve_json):
    logger.debug("Reading nodes, length: "+str(len(nodes)))
    for i in range(0,len(nodes)):
        node=nodes[i]["children"]
        if len(node)>0 and nodes[i]["operator"]=="OR":
            logger.debug("child node found, length: "+str(len(node)))
            get_cpe_cve_map_form_nodes(cve_id,node,cpe_cve_json)
        else:
            pass
            logger.debug("No child found")
        logger.debug("digging cpe_match, length:  "+str(len(nodes[i]["cpe_match"])))#+" values: \n"+str(nodes[i]["cpe_match"]))
        # logger.debug("cpe_match vulnerable value: "+str(type(nodes[i]["cpe_match"][0]["vulnerable"])))
        for m_cpe in nodes[i]["cpe_match"]:
            if m_cpe["vulnerable"]:
                logger.debug("vulnerable is true "+str(m_cpe["cpe23Uri"]))
                logger.debug("digging cpe_name, type: "+str(type(m_cpe["cpe_name"]))+"  length:  "+str(len(m_cpe["cpe_name"])))
                for cpeuri in m_cpe["cpe_name"]:
                    cpe_name=cpeuri["cpe23Uri"]
                    logger.debug("got cpe name: "+str(cpe_name))
                    try:
                        cpe_cve_json[cpe_name].append(cve_id)
                        
                    except KeyError:
                        logger.debug("cpe not present in cpe_cve_json dict ,creating key")
                        cpe_cve_json[cpe_name]=[]
                        cpe_cve_json[cpe_name].append(cve_id)
                if len(m_cpe["cpe_name"])==0:
                    logger.debug("0 no cpe's in cpe_name, taking cpe from URI")
                    cpe_name=m_cpe["cpe23Uri"]
                    try:
                    
                        cpe_cve_json[cpe_name].append(cve_id)
                        
                        logger.debug("cve added to the cpe_cve_json dict: "+str(cve_id))
                    except KeyError:
                        logger.debug("cpe not present in cpe_cve_json dict ,creating key")
                        cpe_cve_json[cpe_name]=[]
                        cpe_cve_json[cpe_name].append(cve_id)
            else:
                pass
                logger.debug("vulnerable is false "+str(m_cpe["cpe23Uri"]))
                              
                    # break
        #     break
        # break
            

def get_cve_to_cpe_mapping_from_NVD(cpe3,start_index,reliable,actual_cpe):
    
    cpe3=str(cpe3).replace("::",":*:")
    logger.debug("Starting the NVD search for cpe: "+str(cpe3))
    
    converted_matched=True
    skipped_cpe_list = []
    cpe_cve_json = {}  
    cpe_cve_mapped={}  
    
    url = "https://services.nvd.nist.gov/rest/json/cves/1.0?cpeMatchString=" + cpe3 + "&resultsPerPage=2000&addOns=dictionaryCpes&startIndex="+str(start_index)
    logger.info("Starting a new CPE search ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
    logger.info("url:"+ url)
    
    retries = 1
    success = False
    while not success:
        try:
            resp = requests.get(url, timeout=120)
            jsonresponse = resp.json()
            
            # with open("D:\\1.json","r") as f:
            #     resp=f.read()
            # jsonresponse= json.loads(resp)
            
            
            success = True
            logger.info("got")
        except Exception:
            wait = retries * 10
            logger.exception( 'Error! Waiting '+ str(wait)+' secs and re-trying...')
            time.sleep(wait)
            retries += 1
            if(retries == 10):
                err_msg = "following cpe skipped::::::::::::::::::::::::::::::::::::::::::::::::::::::::::" + cpe3
                skipped_cpe_list.append(cpe3)
                logger.error(err_msg)
                return None,converted_matched
    if(resp and jsonresponse):
        cpe_no = int(jsonresponse["totalResults"])
            
        if(not cpe_no):
            err_msg = "ERROR:::No CPE found on searching the cpe: " + cpe3 + " from NVD for,  Skipping this NSE.\n"
            logger.error(err_msg)
            skipped_cpe_list.append(cpe3)
            return None,converted_matched
        elif start_index+2000 < int(cpe_no):
            print("llllloooooooooooooookkkkkk out",start_index)
            err_msg = "ERROR:::more than 2000 cpes for" + cpe3 + " from NVD for,. Skipping this NSE.\n"
            logger.critical(err_msg)
            skipped_cpe_list.append(cpe3)
            # return None,converted_matched
        if(cpe_no):
            suc_msg =":::Found " + str(cpe_no) + " CVEs from NVD for the NSE file based on cpe3:" + cpe3
            # print(suc_msg)
            logger.info(suc_msg)
            for cve_count in range(0,cpe_no):
                cve_id=jsonresponse["result"]["CVE_Items"][cve_count]["cve"]["CVE_data_meta"]["ID"]
                logger.debug("Got cve_id "+str(cve_id)+" and cve_count: "+str(cve_count))
                try:
                    if re.search(r"\*\* DISPUTED \*\*",jsonresponse["result"]["CVE_Items"][cve_count]["cve"]["description"]["description_data"][0]["value"]):
                        logger.info("Disputed cve so, Skipping this CVE"+str(cve_id))
                        continue
                except Exception:
                    logger.exception("Exception happened while reading the cve description")
                    
                nodes=jsonresponse["result"]["CVE_Items"][cve_count]["configurations"]["nodes"]
                # logger.debug("got nodes, length:  "+str(len(nodes))+"  value:  \n"+str(nodes))
                
                get_cpe_cve_map_form_nodes(cve_id,nodes,cpe_cve_json)
                logger.debug("Got the cpe_cve_json dict ..., length: "+str(len(cpe_cve_json.keys())))
                
                for key in cpe_cve_json:
                    cpe=str(key)
                    logger.debug("Got cpe from dict:"+ str(cpe))
                    strippos = str(cpe).find(':*')
                    if strippos < 0:
                        strippos = len(str(cpe))
                    if re.search(r"[^:*]", str(cpe)[strippos:]) != None:
                        strippos = len(str(cpe))
                        cpe=cpe.replace(":-:",":*:")
                    cpe=cpe[:strippos]
                    if cpe.endswith(":-"):
                        cpe=cpe[:-2]
                    cpe_split=str(cpe).split(":")
                    if cpe.endswith(":"):
                        cpe=cpe[:-1]
                    if len(cpe_split)<6:
                        logger.debug("cpe does not have version, so skipping  "+str(cpe))
                        continue
                    elif (cpe_split[5]=="" or cpe_split[5]=="-" or cpe_split[5]=="*"):
                        logger.debug("cpe does not have version, so skipping  "+str(cpe))
                        continue
                    logger.debug("stripped and ready cpe: "+str(cpe))
                    if reliable=="yes":
                        if len(cpe3.split(":"))<6:
                            if  not re.search(cpe3+".*",cpe):
                                logger.debug("cpe from nse not didn't match with converted cpe"+str(cpe3))
                                if  not re.search(actual_cpe+".*",cpe):
                                    logger.debug("cpe from nse not didn't match with actual cpe also"+str(actual_cpe))
                                    continue
                            else:
                                logger.debug("<6 cpe matched "+cpe3+" with got cpe "+cpe)
                        else:
                            t_cpe3=cpe3.replace("*",".*")
                            if  not re.search(t_cpe3+".*",cpe):
                                logger.debug("*'s changed to .* but still didn't match"+str(t_cpe3))
                                if not re.search(actual_cpe+".*",cpe):
                                    logger.debug("cpe from nse not didn't match with actual cpe also"+str(actual_cpe))
                                    continue
                            else:
                                logger.debug(">6 cpe matched "+cpe3+" with got cpe "+cpe)
                    
                    elif reliable=="no":
                        if not re.search(cpe3[:-1]+".*",cpe):
                            logger.debug("cpe from nse not didn't match with converted cpe"+str(cpe3))
                            # converted_matched=False
                            continue
                    logger.debug("Adding this cpe: "+str(cpe))
                    cpe_cve_mapped[cpe]=cpe_cve_json[key]
            return cpe_cve_mapped,converted_matched
        else:
            logger.debug("No cve found for "+str(cpe3))
            return None,converted_matched
                    
                # break
    else:
        logger.error("jsonresonse not in good condition to read")
        return None,converted_matched
                
                



def main():
    cpe3 = ""
    status = ""
    file_path = ""
    fileopened = ""
    nmap_nse_data = ""
    cve_list = []
    skipped_nse_list = []
    skipped_cpe_list = []
    unreliable_jsons = []
    dynamic_jsons=[]
    not_converted_list=[]
    not_matched_list=[]
    skipped_cpe_dic={}

    ################### INPUT NEEDED #######################

    ##Path of all product detection scripts for updating them
    # nse_product_detect_path = ".\\all_nses\\scanned"
    nse_product_detect_path = ".\\all_nses\\nse"

    ###################  END  ##############################



    if(not nse_product_detect_path):
        err_msg = 'PATH ERROR::--> Path for the "Product Detection" NMAP NSE scripts not available. Please add path @nse_product_detect_path (nse_product_detect_path = "/home/shakeel/Downloads/shakeel")  in the "search_CVE_from_cpes_n_add_to_scripts.py" script. Current given nse_product_detect_path is: ' + nse_product_detect_path + "\n"
        
        logger.error(err_msg)
        sys.exit(0)

    if(re.findall("/$", nse_product_detect_path)):
        nse_product_detect_path = nse_product_detect_path.rstrip('/')

    if( not (os.path.isdir(nse_product_detect_path))):
        err_msg = 'PATH ERROR::--> Path for the "Product Detection" NMAP NSE scripts is not proper. Please add path @nse_product_detect_path (nse_product_detect_path = "/home/shakeel/Downloads/shakeel")  in the "search_CVE_from_cpes_n_add_to_scripts.py" script. Current given nse_product_detect_path is: ' + nse_product_detect_path + "\n"
        
        logger.error(err_msg)
        sys.exit(0)
        # logger.er

    
    try:
        for root, dirs, files in os.walk(nse_product_detect_path):
            print("hehehehehehehehe start")
            
            for file in files:
                print("filr::::::::::::::::::::::", file)
                nse_file_name = file
                file_path = root + '/' + file
                print("file_pathfile_path:", file_path)
                suc_msg = "\n\nReading file: " + file_path
                print("suc_msg", suc_msg)
                # print("ALL_SUC_MSG")
                # print(ALL_SUC_MSG)               
                logger.info(suc_msg)

                ##Process only _detection.nse and -detect.nse(old) scripts
                if( not (re.findall("-detect", file_path) or re.findall("_detection", file_path))):
                    err_msg = "ERROR:::" + nse_file_name + ". Skipping NMAP NSE script as it does not look like a detection script: \n"                    
                    logger.error(err_msg)
                    skipped_nse_list.append(nse_file_name)
                    continue

                fileopened = open(file_path, "r")
                nmap_nse_data = fileopened.read()
                suc_msg = nse_file_name + ":::Successfully read file: " + file_path  + "\n"               
                logger.info(suc_msg)

                ##Get cpe3 and cpe2 from NSE script so as to search NVD based on it for CVE list for this product
                status2, cpe3, reliable, actual_cpe = get_cpe3_from_nse_data(nmap_nse_data)
                
                if(not status2 ):
                    err_msg = "ERROR:::" + nse_file_name + ". No cpe2.3 was found, so skipping it.\n"
                    logger.error(err_msg)
                    skipped_nse_list.append(nse_file_name)
                    continue
                if not cpe3:
                    err_msg = "ERROR:::" + nse_file_name + ". No cpe2 or cpe3 are not correct, so skipping it.\n"
                    logger.error(err_msg)
                    skipped_nse_list.append(nse_file_name)
                    continue
                suc_msg =  nse_file_name + ":::Found CPE2.3 for :" + file_path + str(reliable)+" "+str(cpe3)+" actual:"+" " +str(actual_cpe)
                logger.info(suc_msg)
                
                cpe_cve_mapped,matched =get_cve_to_cpe_mapping_from_NVD(cpe3,0,reliable,actual_cpe)
                # break
                # """
                try:
                    if len(cpe_cve_mapped)<=0:
                        logger.info("No cpe's or cve's got from NVD so skipping "+nse_file_name)
                        skipped_nse_list.append(nse_file_name)
                        continue
                except Exception:
                    logger.info("No cpe's or cve's got from NVD so skipping "+nse_file_name)
                    skipped_nse_list.append(nse_file_name)
                    continue
                else:
                    logger.info("Got cpe_cve_mapped")
                    cpe_cve_json= cpe_cve_mapped
                    if(cpe_cve_json):
                        json_file_name = nse_file_name.replace(".nse", ".json")
                        if not matched:
                            jsonfilename = "not_matched/" + json_file_name
                        else:
                            if reliable=="yes":
                                jsonfilename = "jsons/" + json_file_name
                            elif reliable=="no":
                                jsonfilename = "dynamic_jsons/" + json_file_name
                        
                        with open(jsonfilename, 'w') as outfile:
                            
                            temp_dict = {}
                            temp_dict["cpe-cve-mapping"] = {}
                            temp_dict["cpe-cve-mapping"]["meta_data"] = {}
                            temp_dict["cpe-cve-mapping"]["meta_data"]["description"] = "This is a CPE2.3::CVE mapping file for SecPod SanerNow version checks."
                            temp_dict["cpe-cve-mapping"]["meta_data"]["copyrights"] = "Copyright (C) 2021 SecPod Technologies"
                            temp_dict["cpe-cve-mapping"]["meta_data"]["revision"] = "1.0"
                            temp_dict["cpe-cve-mapping"]["meta_data"]["creation_date"] = "2021-02-03 12:19:53 (Wed, 03 Feb 2021)"
                            temp_dict["cpe-cve-mapping"]["meta_data"]["last_modification_date"] = "2021-02-03 12:19:53 (Wed, 03 Feb 2021)"
                            temp_dict["cpe-cve-mapping"]["cpe_version_cve_mappings"] = {}
                            temp_dict["cpe-cve-mapping"]["cpe_version_cve_mappings"] = cpe_cve_json
                            json.dump(temp_dict, outfile, sort_keys=False, indent='\t', separators=(',', ': '))
                        suc_msg = nse_file_name + ":::Completed processing from NVD for cpe: '" + cpe3 
                       
                        logger.info(suc_msg)

                    else:
                        err_msg = "ERROR:::Skipping CPE::::::: " + cpe3 + "\n"
                        
                        logger.error(err_msg)
                        skipped_nse_list.append(nse_file_name)

                   
                    # print(cpe_cve_json)
            # break
        logger.info(str(skipped_nse_list))
                    


    except Exception as msg:
                exp_msg = "[-] Exception (%s) occurred while reading file from given Path : " % (msg)
                exp_msg = exp_msg + str(nse_product_detect_path)
                logger.exception(exp_msg)
                sys.exit("Exiting")
    logger.info("skipped nse's: "+str(skipped_nse_list))
    logger.info("not matched list: "+str(not_matched_list) )
    logger.info("not converted"+str(not_converted_list))
    
    logger.info(        "###########################################################################")
    logger.info("####")
    logger.info(        "###########################################################################")
    logger.info(skipped_cpe_dic)
#    if(ALL_ERR_MSG):
#        print_overall_results(ALL_ERR_MSG, "err", skipped_nse_list, updated_list, skipped_cpe_list)
#    elif(ALL_SUC_MSG):
#        print_overall_results(ALL_SUC_MSG, "suc", skipped_nse_list, updated_list, skipped_cpe_list)
if __name__ == "__main__":
    try:
        main()
    except Exception as msg:
        # pass
        logger.exception("[-] Global exception : "+str( msg))
