from sqlalchemy.engine.result import ResultProxy
from selenium import webdriver
import csv
from datetime import datetime, timedelta
import sqlite3
import logging
import time

#SQLALCHEMY - CRIA MÉTODO PARA RETORNAR O RESULTADO DA CONSULTA COMO DICIONÁRIO
def fetchdict(self):
    try:
        l = self.process_rows(self._fetchall_impl())
        self._soft_close()
        return [{key: value for (key, value) in row.items()} for row in l]
    except BaseException as e:
        self.connection._handle_dbapi_exception(
            e, None, None, self.cursor, self.context
        )

ResultProxy.fetchdict = fetchdict

#SELENIUM - CASO O WEBDRIVER NÃO LOCALIZE O ELEMENTO, RETORNA FALSE AO INVÉS DE DAR ERRO
class Chrome(webdriver.Chrome):

    def validar(self,element,todosElementos):
        if todosElementos:
            return element
        if len(element):
            return element[0]
        return False

    def find_element_by_id(self, id_,todosElementos=False):
        element=super().find_elements_by_id(id_=id_)
        return self.validar(element=element,todosElementos=todosElementos)

    def find_element_by_xpath(self, xpath,todosElementos=False):
        element=super().find_elements_by_xpath(xpath=xpath)
        return self.validar(element=element,todosElementos=todosElementos)

    def find_element_by_link_text(self, link_text,todosElementos=False):
        element=super().find_elements_by_link_text(text=link_text)
        return self.validar(element=element,todosElementos=todosElementos)

    def find_element_by_partial_link_text(self, link_text,todosElementos=False):
        element=super().find_elements_by_partial_link_text(link_text=link_text)
        return self.validar(element=element,todosElementos=todosElementos)

    def find_element_by_name(self, name,todosElementos=False):
        element=super().find_elements_by_name(name=name)
        return self.validar(element=element,todosElementos=todosElementos)

    def find_element_by_tag_name(self, name,todosElementos=False):
        element=super().find_elements_by_tag_name(name=name)
        return self.validar(element=element,todosElementos=todosElementos)

    def find_element_by_class_name(self, name,todosElementos=False):
        element=super().find_elements_by_class_name(name=name)
        return self.validar(element=element,todosElementos=todosElementos)

    def find_element_by_css_selector(self, css_selector,todosElementos=False):
        element=super().find_elements_by_css_selector(css_selector=css_selector)
        return self.validar(element=element,todosElementos=todosElementos)


# ERROS DE GRAU LEVE
class MildException(Exception):
    def __init__(self, mensagem, estado, plataforma, prc_id, salvar_log=False):
        self.message = mensagem
        self.estado = estado
        self.plataforma = plataforma
        self.prc_id = prc_id
        self.salvar_log = salvar_log

    def __str__(self):
        if self.message:
            if self.salvar_log:
                hoje = datetime.now()
                dia = hoje.strftime('%d/%m/%Y %H:%M')
                with open('C:\\temp\\log_'+self.estado+'_'+str(self.plataforma)+'.csv', 'a', newline='') as csvfile:
                    spamwriter = csv.writer(csvfile, delimiter=';',
                                            quotechar='"', quoting=csv.QUOTE_MINIMAL)

                    spamwriter.writerow([dia, self.prc_id, self.message])
            return self.message
        return "Erro não crítico"
    pass

# ERROS GRAVES
class CriticalException(Exception):
    def __init__(self, mensagem, estado, plataforma, prc_id, salvar_log=False):
        self.message = mensagem
        self.estado = estado
        self.plataforma = plataforma
        self.prc_id = prc_id
        self.salvar_log = salvar_log

    def __str__(self):
        if self.message:
            if self.salvar_log:
                hoje = datetime.now()
                dia = hoje.strftime('%d/%m/%Y %H:%M')
                with open('C:\\temp\\log_'+self.estado+'_'+str(self.plataforma)+'.csv', 'a', newline='') as csvfile:
                    spamwriter = csv.writer(csvfile, delimiter=';',
                                            quotechar='"', quoting=csv.QUOTE_MINIMAL)

                    spamwriter.writerow([dia, self.prc_id, self.message])
            return self.message
        return "Erro Crítico"
    pass

# ERROS FATAIS
class FatalException(Exception):
    def __init__(self, mensagem, estado, plataforma, prc_id, salvar_log=False):
        self.message = mensagem
        self.estado = estado
        self.plataforma = plataforma
        self.prc_id = prc_id
        self.salvar_log = salvar_log

    def __str__(self):
        if self.message:
            if self.salvar_log:
                hoje = datetime.now()
                dia = hoje.strftime('%d/%m/%Y %H:%M')
                with open('C:\\temp\\log_'+self.estado+'_'+str(self.plataforma)+'.csv', 'a', newline='') as csvfile:
                    spamwriter = csv.writer(csvfile, delimiter=';',
                                            quotechar='"', quoting=csv.QUOTE_MINIMAL)

                    spamwriter.writerow([dia, self.prc_id, self.message])
            return self.message
        return "Erro Fatal"
    pass

# LOGGING - SETAR VALORES PADRÕES NOS CAMPOS DA TABELA
class SystemLogFilter(logging.Filter):
    def __init__(self, **kwargs):
        super().__init__()
        self.fields = kwargs

    def filter(self, record):
        for f in self.fields:
            if not hasattr(record, f):
                setattr(record, f, self.fields[f])
                # record.log_login = self.fields[f]
        return True

# LOGGING - CONECTAR NO SQLITE COM O LOGGING
class SQLiteHandler(logging.Handler):
    '''
    Logging handler for SQLite
    Based on Yarin Kessler's sqlite_handler.py https://gist.github.com/ykessler/2662203#file_sqlite_handler.py
    '''

    def __init__(self, database, table, attributes_list):
        '''
        SQLiteHandler class constructor
        Parameters:
            self: instance of the class
            database: database
            table: log table name
            attributes_list: log table columns
        Returns:
            None
        '''
        #super(SQLiteHandler, self).__init__() # for python 2.X
        super().__init__() # for python 3.X
        self.database = database
        self.table = table
        self.attributes= []
        self.fields = []

        for atr in attributes_list:
            self.attributes.append(atr)
            self.fields.append(attributes_list[atr])

        # Create table if needed
        create_table_sql = 'CREATE TABLE IF NOT EXISTS ' + self.table + ' (' + ((' TEXT, ').join(self.fields)) + ' TEXT);'
        #print(create_table_sql)
        conn = sqlite3.connect(self.database)
        conn.execute(create_table_sql)
        conn.commit()
        conn.close()


    def emit(self, record):
        '''
        Save the log record
        Parameters:
            self: instance of the class
            record: log record to be saved
        Returns:
            None
        '''
        # Use default formatting if no formatter is set
        self.format(record)
        record_values = [record.__dict__[k] for k in self.attributes]
        str_record_values = ', '.join("'{0}'".format(str(v).replace("'", '').replace('"', '').replace('\n', ' ')) for v in record_values)
        #print(str_record_values)
        insert_sql = 'INSERT INTO ' + self.table + ' (' + (', '.join(self.fields)) + ') VALUES (' + str_record_values + ');'
        #print(insert_sql)

        for attempt in range(50):
            try:
                conn = sqlite3.connect(self.database, timeout=30.0)
                cur = conn.cursor()
                cur.execute(insert_sql)
                conn.commit()
                cur.close()
                conn.close()
                del cur
                del conn
                break
            except sqlite3.OperationalError:
                time.sleep(1)

        # conn = sqlite3.connect(self.database)
        # conn.execute(insert_sql)
        # conn.commit()
        # conn.close()