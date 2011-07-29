#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Daemon de alarme
# Roda a cada boot (/etc/init.d) e recebe as mensagens do aa
# 
# [aad] <--------------- aaa (recebe do servidor alarmes e passa para aa)

from time import time
from socket import *
from os import system

def notifica(msg):
    agora = int(time())
    system("notify-send AA '%s'" % msg)
    system("espeak -w /tmp/out%s.wav '%s'" % (agora, msg))
    system("aplay -q /tmp/out%s.wav" % agora)

if __name__=="__main__":
    tempo_inicio = time()
    
    # conexão com servidor
    host = "localhost"
    port = 4040
    buf = 1024
    addr = (host, port)

    UDPSock = socket(AF_INET,SOCK_DGRAM)
    UDPSock.bind(addr)

    # fica escutando as msgs do aa
    while True:
	data, addr = UDPSock.recvfrom(buf)
	if not data:
            print "Cliente desconectou!"
	else:
            print 'Mensagem recebida do controle: %s' % data
            notifica(data)

    # Close socket
    UDPSock.close()
