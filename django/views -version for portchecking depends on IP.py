# coding:utf-8
import subprocess
import time
import sys
import re
import paramiko
import socks
import time
import socket
import telnetlib
import io
from time import sleep
from tqdm import tqdm
from time import strftime, localtime
from django.http import HttpResponse,JsonResponse
from django.shortcuts import render
import json




def index(request):
    return render(request, 'index.html')

def chasing(request):

    ip_address = request.GET['a']
    s = io.StringIO()
    filename = (time.strftime("%Y%m%d%H%M%S", localtime()) +'_'+ip_address+ '.txt')
    f = open(filename, 'w')
    f.write('Tracert' + '\n')
    f.close()

    i = 0
    print(time.strftime("\nDate: %d %B %Y"))
    s.write(time.strftime("\nDate: %d %B %Y"))
    ############################ping test
    pping = subprocess.Popen(["ping", ip_address], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    pping.wait()
    ipping = []
    while True:
        line = pping.stdout.readline()
        ipping.append(line)
        if not line:
            break
    ipping = re.search('Received = .', str(ipping)).group()
    valueping = ipping.replace('Received = ', '')
    if int(valueping) > 0:
        p = subprocess.Popen(["tracert", ip_address], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        p.wait()
        ip = []
        while True:
            line = p.stdout.readline()
            ip.append(line)
            if not line:
                break
        # print(ip)
        ipnew = []
        for ipstring in ip:
            ipstringex = str(ipstring)
            print(ipstringex)
            s.write(ipstringex)
            ipstringex = re.findall(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', ipstringex)
            # print(ipstringex)
            ipstringex = str(ipstringex)
            ipstringex = ipstringex.replace('[', '').replace(']', '').replace('\'', '').replace('\'', '')
            # print(ipstringex)
            ipnew.append(ipstringex)
        while '' in ipnew:
            ipnew.remove('')
        print(ipnew)
        s.write(str(ipnew))
        # write(str(ipnew))
        print('GW device')
        print(ipnew[(len(ipnew) - 2)])
        s.write(ipnew[(len(ipnew) - 2)])
        # write(ipnew[(len(ipnew)-2)])
        hostname = ipnew[(len(ipnew) - 2)]
        dest = ipnew[(len(ipnew) - 1)]
        # hostname = str.encode(hostname)
        # print (type(hostname))
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, 'socks5 bastion ip', portnumber, False, 'username', 'password')
        socket.socket = socks.socksocket
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:  # for core switch
            ssh.connect(hostname, port=22, username='username', password='password', timeout=5)

            remote_conn = ssh.invoke_shell()
            remote_conn.send('enable\n')
            time.sleep(1)
            remote_conn.send('enable password\n')

            time.sleep(1)
            remote_conn.send('terminal length 0\n')
            time.sleep(5)
            ####################################################### for MAC

            remote_conn.send('show ip arp ' + dest + ' | in ' + dest + '\n')
            time.sleep(15)
            interfacebrief = remote_conn.recv(65535)

            interfacebrief = interfacebrief.decode()
            print(interfacebrief)
            s.write(interfacebrief)
            MACinfo = (re.search('Internet .*\n', interfacebrief)).group()
            MACinfo = MACinfo.split(' ')
            while '' in MACinfo:
                MACinfo.remove('')
            print(MACinfo)
            s.write(str(MACinfo))
            MAC = str(MACinfo[3])
            # print(type(MAC))
            # print('MAC ADDRESS')
            print('MAC ADDRESS is %s' % (MAC))
            s.write('MAC ADDRESS is %s' % (MAC))
            Vlaninterface = str(MACinfo[5])
            Vlaninterface = re.search('GigabitEthernet.*\.',Vlaninterface)  # for Gigabit subinter, still need to consider tengigabit
            ssh.close()
        except (socks.GeneralProxyError):#### telnet
            tn = telnetlib.Telnet(hostname, port=23, timeout=5)
            tn.read_until(('sername:').encode())
            tn.write(('username\n').encode())

            tn.read_until(('assword:').encode())
            tn.write(('password\n').encode())

            tn.write(('enable\n').encode())
            tn.write(('enable password\n').encode())

            tn.write(('terminal length 0\n').encode())
            time.sleep(1)
            tn.write(('show ip arp ' + dest + ' | in ' + dest + '\n').encode())
            time.sleep(15)
            interfacebrief = tn.read_very_eager().decode()
            print(interfacebrief)
            s.write(interfacebrief)
            MACinfo = (re.search('Internet .*\n', interfacebrief)).group()
            MACinfo = MACinfo.split(' ')
            while '' in MACinfo:
                MACinfo.remove('')
            print(MACinfo)
            s.write(str(MACinfo))
            MAC = str(MACinfo[3])
            # print(type(MAC))
            # print('MAC ADDRESS')
            print('MAC ADDRESS is %s' % (MAC))
            s.write('MAC ADDRESS is %s' % (MAC))
            Vlaninterface = str(MACinfo[5])
            Vlaninterface = re.search('GigabitEthernet.*\.',Vlaninterface)  # for Gigabit subinter, still need to consider tengigabit
            tn.close()

        #########################################portchannel
        print('*************start****************')
        while 1 == 1:
            i = i + 1
            try:
                # print(hostname)
                ssh.connect(hostname, port=22, username='username', password='password', timeout=5)

                remote_conn = ssh.invoke_shell()
                remote_conn.send('enable\n')
                time.sleep(1)
                remote_conn.send('enable password\n')

                time.sleep(1)
                remote_conn.send('terminal length 0\n')
                time.sleep(5)
                if Vlaninterface == None:
                    remote_conn.send('show mac address-table | in ' + MAC + '\n')
                    time.sleep(20)
                    portbrief = remote_conn.recv(65535).decode()
                    print(portbrief)
                    s.write(portbrief)
                    # print(type(portbrief))
                    devicehostname = (re.search('\n.*#terminal length 0', portbrief)).group()
                    devicehostname = devicehostname.replace('#terminal length 0', '')
                    portbrief = (re.search('\n.*' + MAC + '.*\w\w\w\w\w\w.*\n', portbrief))
                    if portbrief == None: #################for management ip
                        portbrief = ['this is management ip','None','None']
                        break
                    portbrief = portbrief.group()
                    portbrief = portbrief.replace('\r', '')
                    portbrief = portbrief.replace('\n', '')
                    portbrief = portbrief.split(' ')
                    # print (portbrief)
                    while '' in portbrief:
                        portbrief.remove('')
                    print('the port in show MAC')
                    print(portbrief)
                    s.write(str(portbrief))
                    # port1 = str(portbrief[2])
                    # port2 = str(portbrief[4])
                    port = str(portbrief[len(portbrief) - 1])
                    port = re.sub('\r', '', port)
                    # print(type(port))
                    remote_conn.send('\n')
                    port = str(port)
                    port = port.replace('\n', '')
                    time.sleep(5)
                    print('This is SSH connection')

                else:  # for subinterface
                    print('this is subinterface, that is why we do not show MAC')
                    port = str(Vlaninterface.group())
                    port = port.replace('.', '')
                    Vlaninterface = None

                remote_conn.send('show interfaces ' + port + ' | in Mem\n')

                time.sleep(10)
                ethchannel = remote_conn.recv(65535).decode()

                print(ethchannel)
                s.write(ethchannel)
                ethchannel = re.search('  Members in this channel:.*', ethchannel)

                # print(ethchannel)
                if ethchannel:
                    ethchannel = re.sub(r'  Members in this channel: ', '', ethchannel.group())
                    ethchannel = ethchannel.split(' ')
                    print(ethchannel)
                    ethchannel = str(ethchannel[0])
                else:
                    ethchannel = port
                print(ethchannel)
                s.write(ethchannel)
                ###################################################
                ethchannel = ethchannel.replace('\n', '')
                remote_conn.send('show cdp neighbors ' + ethchannel + ' detail | in IP\n')
                time.sleep(20)
                CDPneighbor = remote_conn.recv(65535).decode()
                print(CDPneighbor)
                s.write(CDPneighbor)
                Platform = re.search('Platform: Cisco IP Phone', CDPneighbor)
                PlatformAP = re.search('(link-local)',CDPneighbor)
                if Platform or PlatformAP:
                    devicehostname = '\n this device link to AP or IP phone'
                    portbrief = ['None', 'None', 'None']
                    break

                CDPaddress = re.search('  IP address:.*', CDPneighbor)
                print(CDPaddress)
                s.write(str(CDPaddress))
                # print('1111')
                if CDPaddress:
                    CDPaddress = re.sub(r'  IP address: ', '', CDPaddress.group())
                    print(CDPaddress)
                    # print(type(CDPaddress))
                    # print(CDPaddress.encode())
                    hostname = CDPaddress.replace('\r', '')
                    print('hostname %s' % (hostname))
                    # print(type(hostname))
                    # print(i)
                    print('*************%d hop******************' % (i))
                    ssh.close()
                else:
                    break
            except (paramiko.ssh_exception.AuthenticationException):
                print('Authentication failed')
            #############################################################telnet
            except (socks.GeneralProxyError):
                tn = telnetlib.Telnet(hostname, port=23, timeout=5)
                tn.read_until(('sername:').encode())
                tn.write(('username\n').encode())

                tn.read_until(('assword:').encode())
                tn.write(('password\n').encode())

                tn.write(('enable\n').encode())
                tn.write(('enable password\n').encode())

                tn.write(('terminal length 0\n').encode())
                time.sleep(1)
                tn.write(('show mac address-table | in ' + MAC + '\n').encode())
                time.sleep(15)
                portbrief = tn.read_very_eager().decode()
                devicehostname = (re.search('\n.*#terminal length 0', portbrief)).group()
                devicehostname = devicehostname.replace('#terminal length 0', '')
                portbrief = (re.search('\n.*' + MAC + '.*\w\w\w\w\w\w.*\n', portbrief))
                if portbrief == None:#################for management ip
                    portbrief = ['this is management ip','None','None']
                    break
                portbrief = portbrief.group()
                portbrief = portbrief.replace('\r', '')
                portbrief = portbrief.replace('\n', '')
                portbrief = portbrief.split(' ')
                # print (portbrief)
                while '' in portbrief:
                    portbrief.remove('')
                print('the port in show MAC')
                print(portbrief)
                s.write(str(portbrief))
                # port1 = str(portbrief[2])
                # port2 = str(portbrief[4])
                port = str(portbrief[len(portbrief) - 1])
                port = re.sub('\r', '', port)
                # print(type(port))
                # remote_conn.send('\n')
                port = str(port)
                port = port.replace('\n', '')
                time.sleep(5)

                tn.write(('show interfaces ' + port + ' | in Mem\n').encode())

                time.sleep(10)
                ethchannel = tn.read_very_eager().decode()
                # print(portchannel)

                # portchannel=portchannel.split('\n')
                # ethchannel = str(portchannel[11])
                print(ethchannel)
                s.write(ethchannel)

                ethchannel = re.search('  Members in this channel:.*', ethchannel)

                # print(ethchannel)
                if ethchannel:
                    ethchannel = re.sub(r'  Members in this channel: ', '', ethchannel.group())
                    ethchannel = ethchannel.split(' ')
                    print(ethchannel)
                    s.write(str(ethchannel))
                    ethchannel = str(ethchannel[0])
                else:
                    ethchannel = port
                print(ethchannel)
                s.write(ethchannel)
                ###################################################
                ethchannel = ethchannel.replace('\n', '')
                tn.write(('show cdp neighbors ' + ethchannel + ' detail | in IP\n').encode())
                time.sleep(15)
                CDPneighbor = tn.read_very_eager().decode()
                print(CDPneighbor)
                s.write(CDPneighbor)
                Platform = re.search('Platform: Cisco IP Phone', CDPneighbor)
                PlatformAP = re.search('(link-local)', CDPneighbor)
                if Platform or PlatformAP:
                    devicehostname = '\n this device link to AP or IP phone'
                    portbrief = ['None', 'None', 'None']
                    break
                CDPneighbor = CDPneighbor.split('\n')
                CDPaddress = str(CDPneighbor[1])
                CDPaddress = re.search('  IP address:.*', CDPaddress)
                if CDPaddress:
                    CDPaddress = re.sub(r'  IP address: ', '', CDPaddress.group())
                    print(CDPaddress)
                    s.write(CDPaddress)
                    # print(type(CDPaddress))
                    # print(CDPaddress.encode())
                    hostname = CDPaddress.replace('\r', '')
                    print('hostname %s' % (hostname))
                    # print(type(hostname))
                    # print(i)
                    print('*************%d hop******************' % (i))
                    tn.close()
                else:
                    break
    else:
        devicehostname = '\n Ip is not reachabel'
        portbrief = ['None','None','None']
################################
    print('final' * 20)
    print(portbrief)
    print(devicehostname)
    devicehostname = devicehostname.replace('\n', '')
    portbrief.insert(0, devicehostname)
    portbrief.insert(0,ip_address)
    elements = {'Query IP':portbrief[0],'switch': portbrief[1], 'VLAN': portbrief[2], 'MAC': portbrief[3],
                'Port': portbrief[len(portbrief) - 1]}
    print(elements)
#################################
    f = open(filename, 'a')
    f.write(s.getvalue())
    f.close()
    #return HttpResponse(s.getvalue(),content_type='application/xhtml+xml')
    #return HttpResponse( json.dumps(elements))
    return render(request,'home.html',{'elements':elements})