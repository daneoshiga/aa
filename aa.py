#!/usr/bin/env python
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

import sys, os, time, atexit, urllib, urllib2, json, io
from signal import SIGTERM
import ConfigParser

guide = """
_.__o_oOoOo[ AA ]oOoOo_o__._

Usage:

   aa config <config> <value> ... sets the config value
   aa start                   ... starts the work session of the day
   aa shout <message>         ... alerts what he is doing now (online)
   aa post <message>          ... alerts what he is doing now (offline)
   aa stop                    ... stops the work session of the day
   aa status                  ... checks daemon status

Remember, you have to configure your nickname before start:

   aa config user.nickname <YOUR NICKNAME HERE>
"""

configuration = ConfigParser.RawConfigParser()
__init = """
[user]
nickname=
email=
tick=900

[server]
url=http://nightsc.com.br/aa/novo_log.php
"""

def init_config():
    """Checks if configuration file exists, case not creates one with initial layout"""
    try:
        open(__get_config_file())
    except IOError:
        configuration.readfp(io.BytesIO(__init))
        #FIXME implement with dictionaries maybe
        __save()

def __save():
    """Saves configuration options to file"""
    with open(__get_config_file(), "wb") as f:
        configuration.write(f)

def __get_config_file():
    """Gets configuration file name"""
    return os.getenv('HOME')+'/.aaconfig'

def config(params):
    """Receives a list with attribute and value.
    Parses attribute for section information and saves value associated."""
    configuration.read(__get_config_file())
    #if section user not present, then create config file with initial layout
    if not configuration.has_section('user'):
        init_config()
    #checks if params is the right size
    if len(params) == 2:
        attribute, value = params
        #if attribute is like section.attribute parses it
        if attribute.count('.') == 1:
            section, attribute = attribute.split('.')
            #if section does not exist creates it
            if not configuration.has_section(section):
                configuration.add_section(section)
            #else set correspondent value
            configuration.set(section, attribute, value)
        else:
            #if no section is specified, add attribute to user section
            configuration.set('user', attribute, value)
        __save()

def get(params):
    """Receives a list with section and attribute name and returns the correspondent value"""
    configuration.read(__get_config_file())
    if (len(params)) == 2:
        section, attribute = params
        try:
            return configuration.get(section, attribute)
        except ConfigParser.NoOptionError:
            pass
    return None

#
# Generic Double-fork based Daemon
#

class Daemon:
    """
    A generic daemon class. From Sander Marechal 
      <http://www.jejik.com/authors/sander_marechal/>

    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        Do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        or http://code.activestate.com/recipes/66012-fork-a-daemon-process-on-unix/
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("[AA] Fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("[AA] Fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile,'w+').write("%s\n" % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

            if pid:
                message = "[AA] pidfile %s already exists. Daemon already running?\n"
                sys.stderr.write(message % self.pidfile)
                sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """

        pid = self.getpid()
        if not pid:
            message = "[AA] pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
                else:
                    print str(err)
                    sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
        pass

    def getpid(self):
        # Get the pid from the pidfile
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
        return pid

#
# AA Daemon
#

class AADaemon(Daemon):
    """
    The AA daemon. The function run() runs forever notifying the user about the remaining time of
    his session.
    """
    def run(self):
        """
        This method runs forever (note the while true loop), notifying the user every N seconds.
        """
        self.logger = AALogger()

        avisos_padroes = 0
        avisos_tick = 0
        inicio = time.time()
        atual = time.time()
        self.notify('Your session has started. Programming, modafoca! :-)')
        while True:
            tick = int(get(['user','tick']))
            prox_aviso_padrao = 10*60 + avisos_padroes * 15*60
            prox_aviso_tick = avisos_tick * tick
            if prox_aviso_padrao < prox_aviso_tick:
                prox_aviso = prox_aviso_padrao
                avisos_padroes += 1
            else:
                prox_aviso = prox_aviso_tick
                avisos_tick += 1
            dormir = prox_aviso + inicio - atual
            #self.logger.log('pad: '+str(prox_aviso_padrao))
            #self.logger.log('tic: '+str(prox_aviso_tick))
            #self.logger.log('prox: '+str(prox_aviso))
            #self.logger.log('dormir: '+str(dormir))
            #self.logger.log('ini-atu: '+str((inicio-atual)))
            if dormir > 0:
                time.sleep(float(dormir))
                atual = time.time()
                self.notify('Tick-tack... '+str(round((atual-inicio)/60.0,2))+\
                            ' minutos')
                self.logger.log('notify') # precisamos notificar isso no log?
                # FIXME: notificar a cada X minutos e informar quanto tempo falta
                # FIXME: como verificar que o usuario logou? fica a cargo do servidor?
    def notify(self, msg):
        """
        A simple wrapper to Ubuntu's notify-send.
        """
        os.system('notify-send "AA [%s]: " "%s"' % (time.strftime("%Y-%m-%d %H-%M-%S"), msg))
        os.system('espeak "%s"' % msg)

#
# AA HTTP Sender
#

class AAHTTPSender:
    """
    The AA HTTP Sender module. It sends the HTTP messages to the server.
    """
    def send(self, msg):
        """
        Sends the msg to the server, encoding it apropriatelly.
        """

        dic = {'json': msg}
        data = urllib.urlencode(dic)
        req = urllib2.Request(get(['server', 'url']), data.encode('ascii'))
        res = urllib2.urlopen(req)
        res.close()

    def send_log(self):
        """
        Uses the send() method to send every line of the ~/.aa.log to the server.
        """
        home = os.getenv('HOME')
        f = open(home + '/.aa.log', 'r')
        alerts = f.read().splitlines()
        f.close()

        d = [{'user': get(['user','nickname']), 'date': a.split(',')[:2][0], 'log': a.split(',')[:2][1]} for a in alerts]
        j = json.dumps(d)
        self.send(j)

#
# AA Logger
#

class AALogger:
    """
    The AA Logger module. It writes every msg to the ~/.aa.log file.
    """
    def __init__(self):
        """
        Creates the logger and set the log file path to ~/.aa.log.
        """
        self.log_filename = os.getenv('HOME') + '/.aa.log'

    def write(self, msg):
        """
        A wrapper to append msg to ~/.aa.log.
        """
        self.log_file = open(self.log_filename, 'a')
        self.log_file.write(msg)
        self.log_file.close()

    def log(self, msg):
        """
        A wrapper to log msg to ~/.aa.log.
        """
        self.write(time.strftime("%Y-%m-%d %H-%M-%S") + ',' + msg + '\n')

    def start(self):
        """
        Starts the logger by creating/overwriting the ~/.aa.log temp file.
        """
        self.log_file = open(self.log_filename, 'w')

#
# Main Function (start here!)
#

if __name__ == "__main__":
    # Creating the AA modules

    # Here we create a logger obj to log every msg to the ~/.aa.log
    logger = AALogger()

    # And this module deals with the HTTP server
    http_sender = AAHTTPSender()

    # Here the daemon that notifies the user every N seconds
    # /tmp/aad.pid has the PID of the forked daemon
    daemon = AADaemon('/tmp/aad.pid')

    # Parsing console arguments
    # FIXME: talvez usar o argparse?
    args = sys.argv[1:]
    if len(sys.argv) > 1:
        # START
        if args[0] in ['start', 'inicio', 'inicia', 'início', 'begin']:
            init_config()
            # checks if the user nickname is defined
            if get(['user','nickname']) is '':
                print '[AA] Please, set your nickname before start hacking. Use: aa config user.nickname <YOUR NICKNAME>.'
                sys.exit(0)

            # start the logger (overwrite or create the ~/.aa.log file)
            logger.start()
            # log a start session action
            logger.log('start')
            # inform to the user at console
            print '[AA] Your session has started. Happy hacking!'
            # fork the daemon and exit
            daemon.start()

        # STOP
        elif args[0] in ['stop','fim', 'finaliza', 'termina', 'end']:
            # log a stop session action
            logger.log('stop')
            # send all the lines at ~/.aa.log file
            http_sender.send_log()
            # the daemon notifies that the session is finished
            daemon.notify('Your session has ended. See ya!')
            # inform to the user at console
            print '[AA] Your session has finished. See ya!'
            # kill the daemon
            daemon.stop()

        # ALERT
        elif args[0] in ['alert', 'informa', 'marca', 'anota', 'msg', 'post'] and args[1]:
            # no matter if we use quotes or not after the "aa alert"
            msg = ''.join([pal+" " for pal in sys.argv[2:]])
            msg = msg.strip()
            # log a alert action
            logger.log('alert ' + msg)
            # inform the user
            print '[AA] New alert: "%s" logged.' % msg

        # SCREAM
        elif args[0] in ['scream', 'say', 'oalert', 'shout'] and args[1]:
            msg = ''.join([pal+" " for pal in sys.argv[2:]])
            msg = msg.strip()
            # log a scream action
            logger.log('shout ' + msg)
            # send the msg to the HTTP server, so it'll be online imediatelly!
            j = json.dumps([{'user': get(['user','nickname']), 'date': time.strftime("%Y-%m-%d %H-%M-%S"), 'log': 'shout ' + msg}])
            http_sender.send(j)
            # inform the user
            print '[AA] New shout: "%s" logged.' % msg

        # CONFIG
        elif args[0] in ['config', 'configura', 'seta'] and args[1]:
            config(sys.argv[2:])
        elif args[0] in ['status', 'st']:
            if daemon.getpid() is not None:
                print '[AA] daemon is up and running... (pid: %s)' % daemon.getpid()
            else:
                print '[AA] Oh nooo! daemon is not running... Get back to work!!!'

        # UNKNOWN OPTION
        else:
            print'[AA] Unknown option: "%s". Please, try again!' % args[0]
            sys.exit(2)
            sys.exit(0)
    else:
        print guide
        sys.exit(2)
