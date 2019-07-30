#!/usr/bin/env python
import requests
import json

###### User Variables

username = 'admin'
password = 'Arista'
server1 = 'https://192.168.255.50'
baseAPI = server1+'/api/v1/rest/'
neighborIPList = ['192.168.13.7','10.208.1.0']
webhookURL = ''
routeThreshold = 0 # Number of routes to allow out. Will alert at > this int.

###### Rest of script.
connect_timeout = 10
headers = {"Accept": "application/json",
           "Content-Type": "application/json"}
requests.packages.urllib3.disable_warnings()
session = requests.Session()

def login(url_prefix, username, password):
    authdata = {"userId": username, "password": password}
    response = session.post(url_prefix+'/web/login/authenticate.do', data=json.dumps(authdata),
                            headers=headers, timeout=connect_timeout,
                            verify=False)
    if response.json()['sessionId']:
        return response.json()['sessionId']

def logout(url_prefix):
    response = session.post(url_prefix+'/web/login/logout.do')
    return response.json()

def getActiveDevices(url_prefix):
    response = session.get(url_prefix+'/analytics/DatasetInfo/Devices')
    devices = response.json()
    activeDevices = []
    for item in devices['notifications']:
        for switch in item['updates']:
            if item['updates'][switch]['value']['status'] == 'active':
                activeDevices.append({item['updates'][switch]['key']: {'hostname': item['updates'][switch]['value']['hostname']}})
    return activeDevices

def getBGPPeerTables(url_prefix,deviceID):
    response = session.get(url_prefix + deviceID + '/Smash/routing/bgp/bgpPeerInfoStatus/default/bgpPeerStatisticsEntry/')
    if response.json()['notifications']:
        localPeers = response.json()['notifications']
        peerList = []
        for peer in localPeers:
            for peervalue in peer['updates']:
                if peer['updates'][peervalue]['key'] in neighborIPList:
                    peerkey = peer['updates'][peervalue]['key']
                    peerxmit = peer['updates'][peervalue]['value']['bgpPeerAfiSafiStats']['1']['_value']['prefixOut']
                    peerOutput = {peerkey: peerxmit}
                    peerList.append(peerOutput)
        return peerList

def main():
    login(server1, username, password)
    getActiveDevices(baseAPI)
    devices = getActiveDevices(baseAPI)
    for device in devices:
        peerlist = getBGPPeerTables(baseAPI,device.keys()[0])
        if peerlist:
            for peer in peerlist:
                if int(peer.values()[0]) > routeThreshold:
                    print 'Peer '+peer.keys()[0]+' on '+device.values()[0]['hostname']+' is over threshold of '+\
                    str(routeThreshold)+' with '+str(peer.values()[0])+' routes being sent.'
    logout(server1)

if __name__ == "__main__":
  main()
