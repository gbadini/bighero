from Controllers.Clientes.entrantes import *
from Controllers.Clientes.Espaider._espaider import *
import json

# CAPTURA PROCESSOS ENTRANTES DO ESPAIDER
class Entrantes(EntrantesCliente, Espaider):

    def __init__(self):
        super().__init__()
        self.movs = []
        self.ordem_usuario = 0

    def pesquisa_processos(self, base, captura_ocorrencia=True):
        self.abre_contencioso()

        self.gera_relatorio_cadastro(base)
        if captura_ocorrencia:
            self.gera_relatorio_ocorrencias(base)

        # FECHA NAVEGADOR
        self.driver.close()

    def gera_relatorio_cadastro(self, base):
        tipo_data = ('Criado em', 'Cadastrado em',)

        colunas = self.detecta_colunas()
        dados_site = []
        processos = []
        for tb in tipo_data:
            if tb not in colunas:
                raise MildException("Campo de data não localizado", self.uf, self.plataforma, self.prc_id)

            self.preenche_datas(colunas[tb], colunas)
            dados_site, processos = self.captura_linhas(colunas)

        self.limpa_datas(colunas)
        procs_base = Processo.get_processos_by_numero_cadastro(base, processos)
        numeros_base = {}
        for p in procs_base:
            numeros_base[p['prc_numero_processum']] = p

        processos_novos = []
        # processos_existentes = []
        # SEPARA OS PROCESSOS QUE NÃO ESTÃO NA BASE
        for obj in dados_site:
            if obj['prc_numero_processum'] not in numeros_base:
                self.processos_novos.append(obj)
                processos_novos.append(obj)
            # else:
            #     # obj['prc_id'] = sequenciais_base[obj['prc_numero']]['prc_id']
            #     # processos_existentes.append(obj)
            #     processos_existentes.append(numeros_base[obj['prc_numero']]['prc_id'])

        processos_novos = self.check_proc_dup(processos_novos)
        print('processos_novos: ', len(processos_novos))
        Processo.insert_batch(base, processos_novos)

    def limpa_datas(self, colunas):
        div = self.driver.find_element_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[1]/div/div/div/div[' + str(colunas['Criado em']) + ']')
        div.find_element_by_xpath('div[3]/div[1]/div/div/input').clear()
        div.find_element_by_xpath('div[3]/div[2]/div/div/input').clear()

        div = self.driver.find_element_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[1]/div/div/div/div[' + str(colunas['Cadastrado em']) + ']')
        div.find_element_by_xpath('div[3]/div[1]/div/div/input').clear()
        div.find_element_by_xpath('div[3]/div[2]/div/div/input').clear()

    def gera_relatorio_ocorrencias(self, base):
        self.driver.find_element_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[1]/div/div/div[7]/em/button').click()
        self.driver.switch_to.default_content()
        aguarda_presenca_elemento(self.driver, '/html/body/div/div/div[2]/div/iframe')
        iframe = self.driver.find_element_by_xpath('/html/body/div/div/div[2]/div/iframe')
        self.driver.switch_to_frame(iframe)
        datas = self.formata_datas(10, 7)

        campo_pesquisa = self.driver.find_element_by_id('cbModeloFiltroEdt').get_attribute('value')
        if campo_pesquisa != '15 - Processos por andamentos':
            self.driver.find_element_by_id('cbModeloFiltroEdt').clear()
            while self.driver.find_element_by_id('cbModeloFiltroEdt').get_attribute('value') != '':
                self.driver.find_element_by_id("cbModeloFiltroEdt").send_keys(Keys.END)
                self.driver.find_element_by_id("cbModeloFiltroEdt").send_keys(Keys.BACKSPACE)
            self.driver.find_element_by_id('cbModeloFiltroEdt').send_keys('15 - Processos por andamentos')
            self.driver.find_element_by_id('cbModeloFiltroEdt').send_keys(Keys.RETURN)

        aguarda_presenca_elemento(self.driver, 'ProcessoEventos_DataEvento_startDateEdt', tipo='ID')
        self.driver.find_element_by_id('ProcessoEventos_DataEvento_startDateEdt').send_keys(datas[0])
        self.driver.find_element_by_id('ProcessoEventos_DataEvento_endDateEdt').send_keys(datas[1])
        self.driver.find_element_by_xpath('//*[@id="Ok"]/em/button').click()

        self.driver.switch_to.default_content()
        iframe_buscaProcesso = self.driver.find_element_by_xpath('/html/body/form/div/div/div/iframe')
        self.driver.switch_to_frame(iframe_buscaProcesso)

        self.wait_load()

        colunas = self.detecta_colunas()
        dados_site, processos = self.captura_linhas(colunas)

        procs_base = Processo.get_processos_by_numero_cadastro(base, processos)
        numeros_base = {}
        for p in procs_base:
            numeros_base[p['prc_numero_processum']] = p

        processos_novos = []
        processos_existentes = []
        # SEPARA OS PROCESSOS QUE NÃO ESTÃO NA BASE
        for obj in dados_site:
            if obj['prc_numero_processum'] not in numeros_base:
                self.processos_novos.append(obj)
                processos_novos.append(obj)
            else:
                processos_existentes.append(numeros_base[obj['prc_numero_processum']]['prc_id'])

        processos_novos = self.check_proc_dup(processos_novos)
        print('processos_novos: ', len(processos_novos))
        print('processos_existentes', len(processos_existentes))
        Processo.insert_batch(base, processos_novos)
        if len(processos_existentes) > 0:
            Processo.update_batch(base, processos_existentes, {'prc_data_update1': None, 'prc_situacao': 'Ativo'})

    def captura_linhas(self, colunas):
        dados_site = []
        processos = []
        while True:
            self.wait_load()
            trs = self.driver.find_elements_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr')
            for tr in trs:
                prc_numero = tr.find_element_by_xpath('td[' + str(colunas['Numero']) + ']').text
                if prc_numero == '':
                    continue
                prc_numero = prc_numero[:35]
                processos.append(prc_numero)
                prc_autor = corta_string(tr.find_element_by_xpath('td[' + str(colunas['Adverso']) + ']').text,80)
                prc_modulo = tr.find_element_by_xpath('td[' + str(colunas['Natureza']) + ']').text
                prc_objeto1 = tr.find_element_by_xpath('td[' + str(colunas['Objeto']) + ']').text
                prc_situacao = tr.find_element_by_xpath('td[' + str(colunas['Situacao']) + ']').text
                prc_comarca = tr.find_element_by_xpath('td[' + str(colunas['Comarca']) + ']').text
                prc_data = tr.find_element_by_xpath('td[' + str(colunas['Criado em']) + ']').text
                prc_pasta = tr.find_element_by_xpath('td[' + str(colunas['Pasta']) + ']').text
                prc_data = datetime.strptime(prc_data, '%d/%m/%Y %H:%M')

                prc = {'prc_sequencial': 'SEM CONTRATO', 'prc_numero': prc_numero, 'prc_autor': prc_autor,
                       'prc_numero_processum': prc_numero, 'prc_carteira': 5, 'prc_estado': 'BA',
                       'prc_comarca': prc_comarca, 'prc_objeto1': prc_objeto1, 'prc_data_cadastro': prc_data,
                       'prc_data': prc_data, 'prc_modulo': prc_modulo, 'prc_situacao': prc_situacao, 'prc_area': 1, 'prc_pasta': prc_pasta}

                dados_site.append(prc)

            t1 = self.driver.find_element_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[3]/div/div/div[4]/div/div[2]/input').get_attribute('value')
            t2 = self.driver.find_element_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[3]/div/div/div[6]').text.replace('de ','')
            if t1 == t2:
                break

            self.driver.find_element_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[3]/div/div/div[8]/em/button/span[2]').click()

        return dados_site, processos

    def detecta_colunas(self):
        colunas = {}
        try:
            self.driver.maximize_window()
        except:
            pass

        while 'Cadastrado em' not in colunas and 'Numero' not in colunas:
            titulos = self.driver.find_elements_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[1]/div/div/div/div')
            i = 0
            colunas = {}
            for tt in titulos:
                nome = remove_acentos(tt.text)
                i += 1
                colunas[nome] = i

        return colunas

    def preenche_datas(self, id_coluna, colunas):
        self.limpa_datas(colunas)

        datas = self.formata_datas(15,7)
        div = self.driver.find_element_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[1]/div/div/div/div['+str(id_coluna)+']')
        div.find_element_by_xpath('div[3]/div[1]/div/div/input').send_keys(datas[0])
        div.find_element_by_xpath('div[3]/div[2]/div/div/input').send_keys(datas[1])
        div.find_element_by_xpath('div[3]/div[2]/div/div/input').send_keys(Keys.RETURN)
        self.wait_load()

    def abre_contencioso(self):
        # CLICA EM CONTENCIOSO
        xpath = '//*[@id="modProcessos"]/em/button/span'
        aguarda_presenca_elemento(self.driver, xpath)
        self.driver.find_element_by_xpath(xpath).click()

        try_click(self.driver, '//*[@id="WARSAW_ALERT"]/div/em/button')
        self.wait_load()

        # VERIFICA SE A PAGINA FOI CARREGADA
        aguarda_presenca_elemento(self.driver, 'rightCt', tipo='ID')

        # ACESSA O IFRAME DA LISTA E BUSCA DE PROCESSOS
        # xpath_buscaProcessos = '/html/body/form/div[1]/div[2]/div[2]/iframe'
        xpath_buscaProcessos = '/html/body/form/div/div/div/iframe'
        aguarda_presenca_elemento(self.driver, xpath_buscaProcessos)

        iframe_buscaProcesso = self.driver.find_element_by_xpath(xpath_buscaProcessos)
        self.driver.switch_to_frame(iframe_buscaProcesso)

    def check_proc_dup(self, procs):
        seqs = []
        n_procs = []
        for proc in procs:
            if proc['prc_numero_processum'] in seqs:
                continue

            n_procs.append(proc)
            seqs.append(proc['prc_numero_processum'])

        return n_procs