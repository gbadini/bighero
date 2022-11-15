import os
import random
import logging
from Config.customMethods import SQLiteHandler
from Config.customMethods import SystemLogFilter
import requests, time
from configparser import ConfigParser
from pathlib import Path

def create_logger(log_usuario,log_login,log_sistema,log_uf,log_escritorio,log_prc_id=''):
    current_filename = 'log_bighero'
    my_database = current_filename + '.db'
    my_table = 'log'
    config = ConfigParser()
    base_dir = Path(__file__).resolve().parent.parent
    config.read(str(base_dir.joinpath('local.ini')))
    if config.has_option('form', 'ip'):
        log_ip = config.get('form', 'ip')
    else:
        log_ip = requests.get('https://api.ipify.org/').text
        if log_ip.find('erros') > -1:
            time.sleep(1)
            log_ip = requests.get('https://api.ipify.org/').text
            if len(log_ip) > 20:
                log_ip = '201.47.170.196'


    print(log_ip)
    logger = logging.getLogger(__name__)
    logger.addFilter(SystemLogFilter(log_usuario=log_usuario, log_login=log_login, log_sistema=log_sistema, log_uf=log_uf, log_escritorio=log_escritorio, log_prc_id=log_prc_id, log_ip= log_ip))
    logger.setLevel(logging.DEBUG)

    if not logger.hasHandlers():
        attributes_list = {'asctime': 'log_data', 'levelname': 'log_nivel', 'message': 'log_mensagem', 'log_usuario': 'log_usuario', 'log_login': 'log_login', 'log_sistema': 'log_sistema', 'log_uf': 'log_uf', 'log_escritorio': 'log_escritorio', 'log_prc_id': 'log_prc_id', 'log_ip': 'log_ip'}
        formatter = logging.Formatter('%(' + ((')s' + '|' + '%(').join(attributes_list)) + ')s')

        console_handler = logging.StreamHandler()
        # console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)

        sql_handler = SQLiteHandler(database=my_database, table=my_table, attributes_list=attributes_list)
        # sql_handler.setLevel(logging.INFO)
        sql_handler.setFormatter(formatter)

        all_file_handler = logging.FileHandler(current_filename + '.log')
        all_file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(sql_handler)
        # logger.addHandler(error_file_handler)
        logger.addHandler(all_file_handler)
        # logger.addHandler(critical_file_handler)

        # logger.info('Generate some random integers')
    return logger
