#!/usr/bin/env python

#########################################################
### Script name:
### Author: BCA Y MLS
### Department: WAF SOC
### Version: 3.2
########################################################

import requests
import argparse
import getpass
import sys
import warnings
import datetime
import time
import json

#Credentials

#-------------------IMPERVA API--------------------------

print ("Introduce tu API y tu KEY: ")
if sys.stdin.isatty():
   IMPERVA_API_ID = input("Username: ")
   IMPERVA_API_KEY = getpass.getpass("Password: ")
else:
   IMPERVA_API_ID = sys.stdin.readline().rstrip()
   IMPERVA_API_KEY = sys.stdin.readline().rstrip()

IMPERVA_headers = {
    "x-API-key": IMPERVA_API_KEY,
    "x-API-id": IMPERVA_API_ID,
    "Content-Type" : "application/json"
}
IMPERVA_URL_PREFIX = "https://my.imperva.com/api/prov/v1" #Consulta a la API V1
IMPERVA_URL_PREFIX_V3 = "https://api.imperva.com/certificates/v3" #Consulta a la API V3
Globalcheck = False
#--------------------------------------------------------
print("Entity, Site, Custom Certificate Expiration Date, Scheduled Renewal Date, Imperva Certificate Status, Imperva Certificate Expiration, Globalsign TXT")
parser=argparse.ArgumentParser()
parser.add_argument("--accountid", type=str, help="ID of the account in Imperva")

args = parser.parse_args()

def getAccountName (accountid):
    response=""
    payload =""
    feature = "/account"
    url = IMPERVA_URL_PREFIX + feature + "?account_id=" + str(accountid)
    try:
        response = requests.post(url, headers=IMPERVA_headers, data=payload, verify=False)
        jsonresp = json.dumps(response.json())
        response_dict= json.loads(jsonresp)
        return response_dict["account"]["account_name"]
    except:
        print("API interaction error: GetAccountName" + str(response))


def getv3date (siteid):
    V3expirationdate = ""
    response=""
    payload=""
    feature = "/certificates"
    url = IMPERVA_URL_PREFIX_V3 + feature + "?extSiteId=" + str(siteid)
    global Globalcheck
    try:
        response = requests.get(url, headers=IMPERVA_headers, data=payload, verify=False)
        jsonresp = json.dumps(response.json())
        response_dict = json.loads(jsonresp)
        for i in range(len(response_dict["data"])):
            for z in range(len(response_dict["data"][i]["sans"])):
                if response_dict["data"][i]["sans"][z]["status"]=="PUBLISHED":
                    V3expirationdate = response_dict["data"][i]["sans"][z]["expirationDate"]

                    Globalcheck = False
                    return V3expirationdate

    except:
        pass
        try:
            response = requests.get(url, headers=IMPERVA_headers, data=payload, verify=False)
            jsonresp = json.dumps(response.json())
            response_dict = json.loads(jsonresp)

            verificationtxt = response_dict["data"][0]["sans"][0]["verificationCode"]

            Globalcheck = True
            return verificationtxt

        except:
            print("No hay txt en " + str(siteid))



def listSitesforAccount (account_id):
    feature="/sites/list"
    payload=""
    page_id=0
    count_item_per_page = 20
    finished_pagination = False

    while not finished_pagination:
        url = IMPERVA_URL_PREFIX + feature + "?page_size=" + str(count_item_per_page) + "&page_num=" + str(
            page_id) + "&account_id=" + str(account_id)
        response = requests.post(url, headers=IMPERVA_headers, data=payload, verify=False)
        jsonresp = json.dumps(response.json())
        response_dict = json.loads(jsonresp)

        if response_dict["sites"] == []:
            finished_pagination = True
            break

        for i in range(len(response_dict["sites"])):
            try:

                autogenerado = False
                accountname = getAccountName(response_dict["sites"][i]["account_id"])
                site_id = response_dict["sites"][i]["site_id"]
                getvalidate = response_dict["sites"][i]['ssl']['generated_certificate']['validation_status']
                gencertexpdate = getv3date(site_id)
                certexpdate1 = response_dict["sites"][i]['ssl']['custom_certificate']['expirationDate']
                certgenerated = "Autogenerado Imperva"

                if "validation_status" in response_dict["sites"][i]['ssl']['generated_certificate']:
                    getvalidate = response_dict["sites"][i]['ssl']['generated_certificate']['validation_status']
                    autogenerado = True
                    if Globalcheck == True:

                        print(str(accountname) + "," + response_dict["sites"][i][
                            "domain"] + "," + datetime.datetime.fromtimestamp(int(certexpdate1 / 1000)).strftime(
                            '%d/%m/%Y %H:%M:%S') + ",," + (getvalidate) + ",," + str(gencertexpdate))
                        pass


                    print(str(accountname) + "," + response_dict["sites"][i]["domain"] + "," + datetime.datetime.fromtimestamp(int(certexpdate1 / 1000)).strftime(
                        '%d/%m/%Y %H:%M:%S') + ",," + (getvalidate) + "," + datetime.datetime.fromtimestamp(int(gencertexpdate / 1000)).strftime(
                        '%d/%m/%Y %H:%M:%S'))

                else:
                    print(response_dict["sites"][i]["domain"] + "," + str(
                        accountname) + "Error en loop 1")
            except:
                pass
            try:
                certexpdate = response_dict["sites"][i]['ssl']['custom_certificate']['expirationDate']
                accountname = getAccountName(response_dict["sites"][i]["account_id"])
                cert = response_dict["sites"][i]['ssl']['custom_certificate']['active']
                if (str(cert) == 'True') and autogenerado == False:
                    certgenerated = "Custom Certificate"
                    print(str(accountname) + "," + response_dict["sites"][i]["domain"] + "," + datetime.datetime.fromtimestamp(int(certexpdate / 1000)).strftime(
                        '%d/%m/%Y %H:%M:%S') + ",,,,")

#                         [En este segundo loop SÍ entraba]
#                else:
#                    print(response_dict["sites"][i]["domain"] + "," + str(
#                        accountname) + "," + datetime.datetime.fromtimestamp(int(certexpdate / 1000)).strftime(
#                        '%d/%m/%Y %H:%M:%S') + "," + "Error en loop 2")
            except:

                print(str(accountname)+","+ response_dict["sites"][i]["domain"] +", No cert")


        page_id += 1




def main():
    warnings.filterwarnings("ignore")
    listSitesforAccount(args.accountid)

if __name__ == '__main__':
    main()