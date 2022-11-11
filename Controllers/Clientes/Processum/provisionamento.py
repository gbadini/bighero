import time
from Controllers.Clientes.provisionamento import *
from Controllers.Clientes.Processum._processum import *
from dateutil.relativedelta import relativedelta

# CLASSE DO LANÇAMENTO DE PROVISIONAMENTO. HERDA OS METODOS DA CLASSE PROCESSUM
class Provisionamento(ProvisionamentoCliente, Processum):

    def __init__(self):
        super().__init__()
        self.ordem_usuario = 2

    def lanca_provisao(self, base, dados, pagamentos, arquivos, url_arquivos):
        modulo = self.driver.find_element_by_id('fDetalhar:moduloAtualDesc').text.strip()
        self.abre_modal_contingencia()

        # IDENTIFICA OS CAMPOS CONFORME O MODULO (JEC OU VC)
        id_select = 'fContingencia:tr3' if modulo == 'JEC' else 'fContingencia:tr4'
        id_input_op = 'fContingencia:__valorProvavel15' if modulo == 'JEC' else 'fContingencia:__valorProvavel17'
        id_input_fin = 'fContingencia:__valorProvavel16' if modulo == 'JEC' else 'fContingencia:__valorProvavel18'
        id_input_op_not = 'fContingencia:__valorProvavel17' if modulo == 'JEC' else 'fContingencia:__valorProvavel15'
        id_input_fin_not = 'fContingencia:__valorProvavel18' if modulo == 'JEC' else 'fContingencia:__valorProvavel16'

        # SOMA OS PROVISIONAMENTOS CASO O PROCESSO TENHA MAIS DE UM PAGAMENTO VINCULADO
        soma_op = 0
        soma_fin = 0
        for pag in pagamentos:
            if pag['pag_prov_op'] is not None:
                soma_op += pag['pag_prov_op']
            if pag['pag_prov_fin'] is not None:
                soma_fin += pag['pag_prov_fin']

        # CASO SEJA ACORDO, SOMENTE É PROVISIONADO O VALOR OPERACIONAL
        # if dados['pag_tipo'] == 'Acordo':
        #     soma_op += soma_fin
        #     soma_fin = 0

        # FORMATA VALORES CONFORME FORMATO PT-BR
        soma_op = format_number_br(soma_op)
        soma_fin = format_number_br(soma_fin)

        # VERIFICA SE EXISTEM VALORES LANÇADOS EM OUTRA CC
        op_site_not = self.driver.find_element_by_id(id_input_op_not).get_attribute('value')
        fin_site_not = self.driver.find_element_by_id(id_input_fin_not).get_attribute('value')
        valores_site = op_site_not
        if fin_site_not != '':
            valores_site += ' | ' + fin_site_not

        if op_site_not != '' or fin_site_not != '':
            raise FatalException('Valores anteriores já lançados: ' + valores_site, self.uf, self.plataforma, self.prc_id)

        # VERIFICA SE JÁ EXISTEM VALORES LANÇADOS E SE OS MESMOS DIVERGEM DO QUE ESTÁ NA BASE
        op_site = self.driver.find_element_by_id(id_input_op).get_attribute('value')
        fin_site = self.driver.find_element_by_id(id_input_fin).get_attribute('value')
        valores_site = op_site
        if fin_site != '':
            valores_site += ' | ' + fin_site

        if (op_site != '' and op_site!=soma_op) or (fin_site != '' and fin_site!=soma_fin):
            raise FatalException('Valores diferentes já lançados: ' + valores_site, self.uf, self.plataforma, self.prc_id)

        trs_arq = len(self.driver.find_elements_by_xpath('//*[@id="fContingencia:dtbAnexoVai:tbody_element"]/tr'))
        valores_lancados = False
        if op_site == soma_op and fin_site == soma_fin:
            valores_lancados = True
            if trs_arq >= len(arquivos):
                if self.reavaliar(dados, False, raise_error=True):
                    self.fecha_modal()
                    return True


        arquivos_lancados = False
        if trs_arq >= len(arquivos):
            arquivos_lancados = True
        else:
            trs_arq = len(self.driver.find_elements_by_xpath('//*[@id="fContingencia:dtbAnexo:tbody_element"]/tr'))
            prev_trs_arq = trs_arq
            for arq in arquivos:
                file_upload = self.driver.find_element_by_id('fContingencia:anexo')
                url_arq = trata_path(url_arquivos + arq['arq_url'])
                try:
                    file_upload.send_keys(url_arq)
                    self.driver.find_element_by_xpath('//*[@id="fContingencia:teste"]/tbody/tr[10]/td[3]/a').click()
                except:
                    raise FatalException("Arquivo não localizado", self.uf, self.plataforma, self.prc_id)

                inicio = time.time()
                while prev_trs_arq == trs_arq:
                    tempoTotal = time.time() - inicio
                    if tempoTotal >= 45:
                        raise MildException("Erro ao lançar arquivo", self.uf, self.plataforma, self.prc_id)
                    trs_arq = len(self.driver.find_elements_by_xpath('//*[@id="fContingencia:dtbAnexo:tbody_element"]/tr'))

                prev_trs_arq = trs_arq

            trs_arq = len(self.driver.find_elements_by_xpath('//*[@id="fContingencia:dtbAnexo:tbody_element"]/tr'))
            if trs_arq >= len(arquivos):
                arquivos_lancados = True

        if not valores_lancados:
            if op_site == '' or fin_site == '':
                self.seleciona_option('1', id_select, tipo='ID', select_by='value')
                self.preenche_campo(soma_op, id_input_op, tipo='ID')
                self.preenche_campo(soma_fin, id_input_fin, tipo='ID')
                valores_lancados = True

        if valores_lancados and arquivos_lancados:
            self.driver.find_element_by_xpath('//*[@id="fContingencia:teste"]/tbody/tr[10]/td[4]/input').click()
            self.detecta_erro(raise_critical=False)

        self.reavaliar(dados, False)
        self.fecha_modal()
        return False