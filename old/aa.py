#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
# Copyright 2011 Lab Macambira
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#-----------------------------------------------------------------------------

# Cliente para enviar mensagens ao servidor
# http://wiki.nosdigitais.teia.org.br/AA_0.0.1

# deps:
# libnotify-bin

import urllib.request
import urllib.parse
import sys
import os
from time import time, strftime
from threading import Timer
import aaconfig

instrucoes = """
AA

Using:

   aa start             = starts the work session of the day
   aa alert <resumo>    = alerts what he is doing now
   aa stop              = stops the work session of the day
   aa config <config> <valor> = seta valor da config
"""

Sent = None
Envi = None


class Sentinela(object):
    """Warnings from time to time"""

    def __init__(self, minutos=15):
        """Give a warning after each minutos"""
        self.minutos = minutos
        self.vezes = -1

    def iniciar(self):
        """Starts to count"""
        #self.timer.start()
        self.avisar()

    def parar(self):
        """Stops to count"""
        self.timer.cancel()
        print("PAROU!!!!!!!!!")

    def avisar(self):
        """Gives the warning and restarts the Timer"""
        self.vezes = self.vezes + 1
        os.system('notify-send "AA:" "WTF are you doing?!\n(Trabalhando há '+\
                  str(self.minutos*self.vezes) + ' minutos)"')
        self.timer = Timer(self.minutos*60, self.avisar)
        self.timer.start()


class Enviador(Sentinela):
    """Sends the data to the server periodically"""

    def avisar(self):
        """Sends data"""
        global Envi
        fim = enviar()
        if not fim:
            self.timer = Timer(self.minutos*60, self.avisar)
            self.timer.start()
        else:
            Sent.parar()

def comeca():
    """Start the session"""
    f = open(os.getenv("HOME")+"/.aa.txt", "w")
    f.close()
    try:
        f = open(os.getenv("HOME")+"/.aaconfig", "r")
    except IOError:
        aaconfig.configura_default()
    os.system("aa daemon &")

def enviar():
    """Sends data to the server"""
    fim = False
    home = os.getenv("HOME")
    f = open(home+"/.aa.txt", "r")
    alertas = f.read().splitlines()
    f.close()
    # FIXME cuidar de possíveis problemas de concorrência
    f = open(home+"/.aa.txt", "w")
    f.close()
    for alerta in alertas:
        # prepare the string
        alerta = alerta.split(',')
        msg = {'user': aaconfig.get_config(['user','nickname']), 'log': alerta[0]+'::'+alerta[1]}
        dados = urllib.parse.urlencode(msg)
        # sends the string
        print("Sending:",alerta[1])
        req = urllib.request.Request('http://nightsc.com.br/aa/novo_log.php',
                                     dados.encode('ascii'))
        res = urllib.request.urlopen(req)
        #pagina = res.read()
        res.close()
        # prepare the flag that will stop the daemon
        if alerta[1] == 'stop':
            fim = True
    return fim

def termina():
    """Stop the session"""
    #enviar()
    pass

# FIXME criar daemon de forma que ele não morra junto com o terminal
def daemonificar():
    """Runs the daemon"""
    global Sent, Envi
    Sent = Sentinela(int(aaconfig.get_config(['user','interval'])))
    Sent.iniciar()
    Envi = Enviador(0.25)
    Envi.iniciar()

def direciona(args):
    """Parse AA arguments"""
    #talvez usar o argparse?
    if args[0] in ['start','inicio', 'inicia', 'início', 'begin']:
        comeca()
        log('start')
        print('[AA] Your session has started. Happy hacking!')
    elif args[0] in ['stop','fim', 'finaliza', 'termina', 'end']:
        # registra hora de fim
        log('stop')
        termina()
        print('[AA] You ended the sesssion and published at ' \
        'http://nightsc.com.br/aa. CYA!')
    elif args[0] in ['daemon']:
        # starts the daemon
        daemonificar()
        print('[AA] Daemon started')
    elif args[0] in ['post','informa', 'marca', 'anota', 'msg'] and args[1]:
        # registra marca no registro iniciado (corrente)
        msg = ''.join([pal+" " for pal in sys.argv[2:]])
        msg = msg.strip()
        log("alert "+msg)
        print('[AA] New alert: "%s" logged.' % msg)
    elif args[0] in ['config','configura','seta'] and args[1]:
        aaconfig.configura(sys.argv[2:])
    else:
        print('Opção "%s" inválida!' % args[0])

def log(msg):
    """Saves messages on the ~/.aa.txt temp file"""

    home = os.getenv('HOME')
    f = open(home+"/.aa.txt","a")

    try:
        #escreve mensagem no arquivo com data/hora
        #FIXME definir melhor formato para data/hora
        f.writelines(strftime("%d-%m-%y %H-%M-%S")+","+msg+"\n")
    finally:
        f.close()
    return






if __name__=="__main__":
    if len(sys.argv) > 1:
        direciona(sys.argv[1:])
    else:
        print(instrucoes)
