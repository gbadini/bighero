import time

from Controllers.Clientes.contingencia import *
from Controllers.Clientes.Processum._processum import *
from dateutil.relativedelta import relativedelta

# CLASSE DO LANÇAMENTO DE CONTINGENCIA. HERDA OS METODOS DA CLASSE PROCESSUM
class Contingencia(ContingenciaCliente, Processum):

    def __init__(self):
        super().__init__()
        self.ordem_usuario = 2

    def lanca_contingencia(self, dados):
        self.abre_modal_contingencia()

        possivel_site = self.driver.find_element_by_id('fContingencia:efwe').get_attribute('value')
        remoto_site = self.driver.find_element_by_id('fContingencia:rwgr').get_attribute('value')
        possivel_base = format_number_br(dados['ctg_valor_possivel'])
        if dados['ctg_valor_remoto'] is None or dados['ctg_valor_remoto'] == 0:
            remoto_base = ''
        else:
            remoto_base = format_number_br(dados['ctg_valor_remoto'])

        if possivel_site == '' and remoto_site == '':
            self.seleciona_option('Ingresso', 'fContingencia:tr1', tipo='ID')
            self.preenche_campo(possivel_base, 'fContingencia:efwe', tipo='ID')
            if remoto_base != '':
                self.seleciona_option('Ingresso', 'fContingencia:tr2', tipo='ID')
                self.preenche_campo(remoto_base, 'fContingencia:rwgr', tipo='ID')

            self.driver.find_element_by_id('fContingencia:_idJsp159').click()
            time.sleep(0.5)
            self.fecha_modal()
            return False

        if possivel_site == possivel_base and remoto_site == remoto_base:
            return True

        valores_site = possivel_site
        if remoto_site != '':
            valores_site = ' | ' + remoto_site

        raise FatalException('Valores anteriores já lançados: ' + valores_site, self.uf, self.plataforma, self.prc_id)





