#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import configparser
import io
import os
import sys

config = configparser.RawConfigParser()

def configura_default():
    config['user'] = {'nickname':'' , 'email': '', 'interval': 15}
    __save()

def __save():
    with open(__get_config_file(), "w") as configfile:
        config.write(configfile)

def configura(params):
    config.read(__get_config_file())
    if not config.has_section('user'):
        configura_default()
    if len(params) == 2:
        attribute, value = params
        if attribute.count('.') == 1:
            section, attribute = attribute.split('.')
            if not (section in config):
                config[section] = {}
            config[section][attribute] = value
        else:
            config['user'][attribute] = value
    #config.set('user', params[0], params[1])
    __save()

def get_config(params):
    config.read(__get_config_file())
    section, attribute = params
    return config[section][attribute]

def __get_config_file():
    return os.getenv('HOME')+'/.aaconfig'

if __name__ == "__main__":
    configura()
