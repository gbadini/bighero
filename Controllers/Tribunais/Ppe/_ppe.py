from Config.helpers import *
from Controllers.Tribunais.primeiro_grau import *
from selenium.webdriver.common.keys import *
from Models.processoModel import *
from Models.acompanhamentoModel import *
import urllib.request
import urllib.parse as urlparse
from urllib.parse import parse_qs

import sys, time, shutil

# CLASSE DA VARREDURA DO PJE. HERDA OS METODOS DA CLASSE PLATAFORMA
class Ppe(PrimeiroGrau):

    def __init__(self):
        super().__init__()
        self.plataforma = 9
        self.movs = []
        self.titulo_partes = get_tipo_partes(grau=2)
        self.titulo_partes['ignorar'] += ('Intimad','Representante Legal')
        # self.intervalo = 30

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc):
        adc = self.audiencias()
        prt = self.partes()
        status_atual = 'Ativo' if self.completo else proc['prc_status']
        adv = self.responsaveis()
        prc = self.dados(status_atual)

        return adc, prt, prc, adv

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''
        if not aguarda_presenca_elemento(self.driver, '//*[@id="avisos-signin"]/div/div[3]/p-footer/button/span[2]'):
            return False

        self.driver.find_element_by_xpath('//*[@id="avisos-signin"]/div/div[3]/p-footer/button/span[2]').click()
        self.driver.find_element_by_id("usuario").send_keys(usuario)
        self.driver.find_element_by_id("password").send_keys(senha)
        self.driver.find_element_by_id("password").send_keys(Keys.ENTER)

        if not aguarda_presenca_elemento(self.driver, '//*[@id="supportedContentDropdownProcesso"]/span'):
            return False

        self.wait(30)

        if try_click(self.driver, '//*[@id="navBar"]/button/span'):
            time.sleep(1)

        # self.driver.execute_script("$('.modal-backdrop').remove();")

        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="supportedContentDropdownProcesso"]/span')))
        except TimeoutException:
            pass

        self.wait(30)

        self.driver.find_element_by_xpath('//*[@id="supportedContentDropdownProcesso"]/span').click()

        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="processo"]/div/a')))
        except TimeoutException:
            pass
        self.driver.find_element_by_xpath('//*[@id="processo"]/div/a').click()
        return True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''

        # self.driver.find_element_by_xpath('//*[@id="buscaProcessosQualquerInstanciaForm"]/fieldset/table/tbody/tr[2]/td[2]/input[2]').click()
        try_click(self.driver, '//*[@id="container-principal"]/ppe-detalhes-processo/ppe-acoes-detalhes-processo/tjrs-header/nav/div[2]/div/button[1]')

        if not aguarda_presenca_elemento(self.driver, 'numeroProcesso', tipo='ID', tempo=3):
            raise MildException("Erro ao buscar processo", self.uf, self.plataforma, self.prc_id, False)

        if not self.driver.find_element_by_id('numeroProcesso').is_displayed():
            self.driver.execute_script("$('#ppe-collapsible1').show()")

        if not aguarda_presenca_elemento(self.driver, 'numeroProcesso', tipo='ID', tempo=3, aguarda_visibilidade=True):
            self.process_main_child = foca_janela(self.process_main_child)
            self.driver.find_element_by_xpath('//*[@id="collapser"]').click()
            # self.driver.execute_script("$('#ppe-collapsible1').show()")
            if not aguarda_presenca_elemento(self.driver, 'numeroProcesso', tipo='ID', tempo=3, aguarda_visibilidade=True):
                raise MildException("Erro ao buscar processo", self.uf, self.plataforma, self.prc_id, False)

        try_click(self.driver, '//*[@id="toasty"]/gx-toast/div/div')

        cnj_tj = 'XXX'
        inicio = time.time()
        while numero_busca != cnj_tj:
            if time.time() - inicio > 15:
                    raise MildException("Erro ao imputar CNJ no campo", self.uf, self.plataforma, self.prc_id)

            try:
                self.driver.find_element_by_id('numeroProcesso').clear()
                for c in numero_busca:
                    self.driver.find_element_by_id('numeroProcesso').send_keys(c)

                cnj_tj = self.driver.find_element_by_id('numeroProcesso').get_attribute('value')
                cnj_tj = cnj_tj.replace('.','').replace('-','').replace('/','').replace(' ','')
            except:
                pass

        self.driver.find_element_by_id("numeroProcesso").send_keys(Keys.ENTER)
        self.wait()

        if not aguarda_presenca_elemento(self.driver, '//*[@id="toasty"]/gx-toast', aguarda_visibilidade=True, tempo=20):
            raise MildException("Tempo de busca expirado", self.uf, self.plataforma, self.prc_id, False)

        msg = self.driver.find_element_by_xpath('//*[@id="toasty"]/gx-toast').text.upper()
        if msg.find('NENHUM REGISTRO') > -1:
            return False

        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="processos-grid"]/div/div/table/tbody/tr[1]/td[5]')))
        except TimeoutException:
            msg = self.driver.find_element_by_xpath('//*[@id="toasty"]/gx-toast')
            if not msg:
                raise MildException("Erro ao localizar processo na busca", self.uf, self.plataforma, self.prc_id, False)

            if msg.text.upper().find('NENHUM REGISTRO') > -1:
                return False

        aguarda_presenca_elemento(self.driver,'//*[@id="processos-grid"]/div/div/table/thead/tr/th[4]')
        achei = False
        ths = self.driver.find_elements_by_xpath('//*[@id="processos-grid"]/div/div/table/thead/tr/th')
        for th in ths:
            if th.text.upper().find('NÚMERO THEMIS') > -1:
                achei = True
                break

        if not achei:
            self.driver.find_element_by_xpath('//*[@id="processos-grid"]/div/ppe-datatable-header/div/div/button').click()
            aguarda_presenca_elemento(self.driver, '//*[@id="processos-grid"]/div/ppe-datatable-header/div/div/div/div', aguarda_visibilidade=True)
            self.driver.find_element_by_xpath('//*[@id="processos-grid"]/div/ppe-datatable-header/div/div/div/div/div[4]').click()

        return True

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        i = 0
        ths = self.driver.find_elements_by_xpath('//*[@id="processos-grid"]/div/div/table/thead/tr/th')
        for th in ths:
            i += 1
            if th.text.upper().find('NÚMERO DO PROCESSO') > -1:
                n1 = self.driver.find_element_by_xpath('//*[@id="processos-grid"]/div/div/table/tbody/tr/td['+str(i)+']').text
                n1 = ajusta_numero(n1)

            if th.text.upper().find('NÚMERO THEMIS') > -1:
                n2 = self.driver.find_element_by_xpath('//*[@id="processos-grid"]/div/div/table/tbody/tr/td['+str(i)+']').text
                n2 = ajusta_numero(n2)

        nb = ajusta_numero(numero_busca)
        if n1 != numero_busca and n2 != nb:
            raise MildException("CNJ diferente na busca", self.uf, self.plataforma, self.prc_id, False)

        return True

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        el = localiza_elementos(self.driver, ('divInfraExcecao','lblAvisoTopolabel',), tipo='ID')
        if el:
            if el.text.upper().find('SEGREDO') > -1:
                return True

        self.confere_cnj(numero_busca)

        return False

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        i = 0
        ths = self.driver.find_elements_by_xpath('//*[@id="processos-grid"]/div/div/table/thead/tr/th')
        for th in ths:
            i += 1
            if th.text.upper().find('MOVIMEN') > -1:
                break

        td = self.driver.find_element_by_xpath('//*[@id="processos-grid"]/div/div/table/tbody/tr/td['+str(i)+']/span')
        if not td:
            if self.driver.find_element_by_id("usuario"):
                raise CriticalException("Sessão Encerrada", self.uf, self.plataforma, self.prc_id, False)

            raise MildException("Última Mov não localizada", self.uf, self.plataforma, self.prc_id)

        td_txt = td.text
        f = td_txt.find('-')

        acp_esp = td_txt[f+1:].strip()
        data_cad = td_txt[:f].strip()
        data_cad = datetime.strptime(data_cad, '%d/%m/%Y')
        return Acompanhamento.compara_mov(base, prc_id, acp_esp, data_cad, self.plataforma, self.grau, rec_id=self.rec_id)

    # CAPTURA ACOMPANHAMENTOS DO PROCESSO
    def acompanhamentos(self, proc_data, completo, base):
        '''
        :param datetime Última movimentação registrada na base
        :param bool Realiza a captura completa das movimentações
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        self.wait()
        self.driver.find_element_by_xpath('//*[@id="processos-grid"]/div/div/table/tbody/tr[1]/td[6]').click()
        if not aguarda_presenca_elemento(self.driver, '//*[@id="campoDetalhesProcesso"]/div[1]/div/span'):
            raise MildException("Erro ao abrir processo", self.uf, self.plataforma, self.prc_id, False)

        cnj = self.driver.find_element_by_xpath('//*[@id="campoDetalhesProcesso"]/div[1]/div[1]/span').text
        themis = self.driver.find_element_by_xpath('//*[@id="campoDetalhesProcesso"]/div[1]/div[2]/span')
        numero_site_themis = 'XXX'
        if themis:
            numero_site_themis = themis.text
        numero_busca = ajusta_numero(proc_data['prc_numero'])
        numero_site_cnj = ajusta_numero(cnj)
        numero_site_themis = ajusta_numero(numero_site_themis)

        numero_busca = ajusta_numero(numero_busca)
        if numero_busca != numero_site_themis and numero_busca != numero_site_cnj:
            raise MildException("Número CNJ Diferente na página", self.uf, self.plataforma, self.prc_id)

        self.movs = []
        movs = []
        self.wait()
        ultima_mov = proc_data['cadastro']
        prc_id = proc_data['prc_id']
        rec_id = proc_data['rec_id'] if 'rec_id' in proc_data else None
        prc_pai = proc_data['prc_id'] if proc_data['prc_pai'] is None else proc_data['prc_pai']
        aguarda_presenca_elemento(self.driver, '//*[@id="campoDetalhesProcesso"]/div[4]/div/span')
        # CONFERE SE O PROCESSO FOI MIGRADO
        if proc_data['prc_migrado'] is None or not proc_data['prc_migrado']:
            alerts = self.driver.find_elements_by_class_name('alert-warning')
            for al in alerts:
                txt = al.text.upper()
                if txt.find('MIGRADO') > -1:
                    self.proc_data['prc_migrado'] = True
                    cnj = localiza_cnj(txt, "(\\d+)(.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(.)([0-9]{4})(\\.)(\\d+)(\\.)(\\d+)(\\-)(\\d+)|([0-9]{20})")
                    if not Processo.processo_existe(base, cnj):
                        print("inserindo processo anexo")
                        np = [{'prc_numero': cnj, 'prc_estado': self.uf, 'prc_autor': proc_data['prc_autor'], 'prc_pai': prc_pai, 'prc_area': 1, 'prc_carteira': proc_data['prc_carteira']},]
                        Processo.insert(base, np)
                        Processo.update_simples(base, prc_id, {'prc_migrado': True})
                        break

        self.driver.execute_script("$('ppe-footer').remove()")
        txt = self.driver.find_element_by_xpath('//*[@id="campoDetalhesProcesso"]/div[4]/div/span').text
        f = txt.find('-')

        acp_esp = txt[f+1:].strip().upper()
        data_cad = txt[:f].strip()
        acp_cadastro = datetime.strptime(data_cad, '%d/%m/%Y')
        acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp, 'acp_tipo': None}
        self.movs.append(acp)

        # BUSCA MOVIMENTAÇÕES DO PROCESSO NA BASE
        lista = Acompanhamento.lista_movs(base, prc_id, self.plataforma, acp_grau=self.grau, rec_id=rec_id)
        achei = False
        esp_site = corta_string(acp_esp)
        for l in lista:
            esp_base = corta_string(l['acp_esp'])
            if acp_cadastro == l['acp_cadastro'] and esp_site.upper() == esp_base.upper():
                achei = True
                # movs.append(acp)
                break

        if not achei:
            movs.append(acp)
            self.movs[0]['novo'] = True

        self.wait()
        if self.driver.find_element_by_xpath('//*[@id="toasty"]/gx-toast/div/div'):
            self.driver.find_element_by_xpath('//*[@id="toasty"]/gx-toast/div/div').click()

        di = 0
        btns = self.driver.find_elements_by_xpath('/html/body/app-root/div/ppe-detalhes-processo/div')
        for btn in btns:
            di += 1
            titulo = btn.text.upper()
            if titulo.find('MOVIMENTO') > -1:
                btn.location_once_scrolled_into_view
                btn.click()
                break

        if not aguarda_presenca_elemento(self.driver,'//*[@id="container-principal"]/ppe-detalhes-processo/div['+str(di)+']/ppe-collapsible/div[2]/ppe-detalhes-processo-movimentos-documentos/div[2]/p-datatable/div/div[1]/div/div[2]/div/table/tbody/tr[1]', aguarda_visibilidade=True):
            txt = self.driver.find_element_by_xpath('//*[@id="container-principal"]/ppe-detalhes-processo/div[' + str(di) + ']/ppe-collapsible/div[2]/ppe-detalhes-processo-movimentos-documentos/div[2]')
            if txt:
                if txt.text.upper().find('NENHUM MOVIMENTO') > -1:
                    return movs

                if txt.text.upper().find('ERRO GENÉRICO') > -1:
                    raise FatalException("Erro genérico ao carregar lista de andamentos", self.uf, self.plataforma, self.prc_id)


        d1 = self.driver.find_element_by_xpath('//*[@id="container-principal"]/ppe-detalhes-processo/div[' + str(di) + ']/ppe-collapsible/div[2]/ppe-detalhes-processo-movimentos-documentos/div[2]/p-datatable/div/div[1]/div/div[2]/div/table/tbody/tr')
        inicio = time.time()
        while not d1 or d1.text.strip() == '':
            if time.time() - inicio > 20:
                raise MildException("Erro ao carregar lista de andamentos", self.uf, self.plataforma, self.prc_id)
            d1 = self.driver.find_element_by_xpath('//*[@id="container-principal"]/ppe-detalhes-processo/div[' + str(di) + ']/ppe-collapsible/div[2]/ppe-detalhes-processo-movimentos-documentos/div[2]/p-datatable/div/div[1]/div/div[2]/div/table/tbody/tr')

        dts = self.driver.find_element_by_xpath('//*[@id="container-principal"]/ppe-detalhes-processo/div[' + str(di) + ']/ppe-collapsible/div[2]/ppe-detalhes-processo-movimentos-documentos/div[2]/p-datatable/div/div[1]/div/div[2]/div/table/tbody/tr/td[1]').text.strip()
        pos = 2 if dts == '' else 1

        i = 0
        movimentos = self.driver.find_elements_by_xpath('//*[@id="container-principal"]/ppe-detalhes-processo/div['+str(di)+']/ppe-collapsible/div[2]/ppe-detalhes-processo-movimentos-documentos/div[2]/p-datatable/div/div[1]/div/div[2]/div/table/tbody/tr')
        for mov in movimentos:
            i += 1

            acp_cadastro = mov.find_element_by_xpath('td['+str(pos)+']').text
            if acp_cadastro == '':
                raise MildException("Erro ao capturar movs: ", self.uf, self.plataforma, self.prc_id)

            acp_cadastro = datetime.strptime(acp_cadastro + ' 00:00:00', '%d/%m/%Y %H:%M:%S')
            acp_esp = mov.find_element_by_xpath('td['+str(pos+1)+']').text

            if i == 1:
                if len(movs) > 0:
                    esp_site = corta_string(acp_esp)
                    esp_mov1 = corta_string(movs[0]['acp_esp'])
                    if movs[0]['acp_cadastro'] == acp_cadastro and esp_site.upper() == esp_mov1.upper():
                        i = 0
                        continue

            esp_site = corta_string(acp_esp)
            capturar = True
            for l in lista:
                esp_base = corta_string(l['acp_esp'])

                if acp_cadastro == l['acp_cadastro'] and esp_site.upper() == esp_base.upper():
                    capturar = False
                    break

            if not capturar and not completo and i >= 10:
                break

            acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp, 'acp_tipo': None}
            if capturar:
                movs.append(acp)

            self.movs.append({**acp, 'novo': capturar})

        if len(self.movs) > 1:
            for m in self.movs[:][1:]:
                if m['acp_esp'] == self.movs[0]['acp_esp'] and m['acp_cadastro'] == self.movs[0]['acp_cadastro']:
                    del self.movs[0]
                    break
            # if self.movs[0]['acp_esp'] == self.movs[1]['acp_esp'] and self.movs[0]['acp_cadastro'] == self.movs[1]['acp_cadastro']:
            #     del self.movs[0]

        if len(movs) > 1:
            for m in movs[:][1:]:
                if m['acp_esp'] == movs[0]['acp_esp'] and m['acp_cadastro'] == movs[0]['acp_cadastro']:
                    del movs[0]
                    break
            # if movs[0]['acp_esp'] == movs[1]['acp_esp'] and movs[0]['acp_cadastro'] == movs[1]['acp_cadastro']:
            #     del movs[0]

        if len(self.movs) == 0:
            raise MildException("Erro ao capturar Movs", self.uf, self.plataforma, self.prc_id)

        return movs

    # CAPTURA AUDIENCIAS DO PROCESSO
    def audiencias(self):
        adcs = []

        txt = self.driver.find_element_by_xpath('//*[@id="campoDetalhesProcesso"]/div[5]/div[4]/span/span').text
        if txt.upper().find('NÃO CONSTA') > -1:
            return adcs

        prp_data = datetime.strptime(txt, '%d/%m/%Y %H:%M')
        return [{'data_mov': prp_data, 'prp_data': prp_data, 'prp_tipo': 'Audiência', 'prp_status': 'Designada'},]

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        prts = {'ativo':[], 'passivo':[], 'terceiro':[]}

        try_click(self.driver, '//*[@id="toasty"]/gx-toast/div/div')

        self.driver.execute_script("window.scrollTo(0,400);")
        btns = self.driver.find_elements_by_xpath('/html/body/app-root/div/ppe-detalhes-processo/div')
        for btn in btns:
            titulo = btn.text.upper()
            if titulo.find('PESSOAS') > -1:
                btn.click()
                break

        # aguarda_presenca_elemento(self.driver, 'ppe-detalhes-processo-pessoas', tipo='TAG_NAME', aguarda_visibilidade=True)
        if not aguarda_presenca_elemento(self.driver, '/html/body/app-root/div/ppe-detalhes-processo/div/ppe-collapsible/div/ppe-detalhes-processo-pessoas/div[2]/p-datatable/div/div[1]/div/div[2]/div/table/tbody/tr', tipo='XPATH', aguarda_visibilidade=True):
            raise MildException("ppe-detalhes-processo-pessoas não localizado", self.uf, self.plataforma, self.prc_id)

        dpp = self.driver.find_elements_by_tag_name('ppe-detalhes-processo-pessoas')
        divp = dpp[0].find_elements_by_xpath('div[2]')
        if len(divp) > 0:
            if divp[0].text.upper().find('NÃO CONTÉM LISTA') > -1:
                return prts

        trs = dpp[0].find_elements_by_xpath('div[2]/p-datatable/div/div[1]/div/div[2]/div/table/tbody/tr')

        for tr in trs:
            tipo = tr.find_element_by_xpath('td[3]').text
            prr_nome = tr.find_element_by_xpath('td[2]').text.strip()
            prr_nome = prr_nome.replace('(em Recuperação Judicial)','')
            if prr_nome == '':
                raise MildException("Nome em branco "+tipo, self.uf, self.plataforma, self.prc_id)
            polo = ''
            if find_string(tipo,self.titulo_partes['ignorar']):
                continue

            if find_string(tipo,self.titulo_partes['ativo']):
                polo = 'ativo'
            if find_string(tipo,self.titulo_partes['passivo']):
                polo = 'passivo'
            if find_string(tipo,self.titulo_partes['terceiro']):
                polo = 'terceiro'
            if polo == '':
                # print("polo vazio "+tipo, '/html/body/app-root/div/ppe-detalhes-processo/div/ppe-collapsible/div/ppe-detalhes-processo-pessoas/div[2]/p-datatable/div/div[1]/div/div[2]/div/table/tbody/tr')
                # time.sleep(999)
                raise MildException("polo vazio "+tipo, self.uf, self.plataforma, self.prc_id)

            prts[polo].append({'prt_nome': prr_nome, 'prt_cpf_cnpj': 'Não Informado'})

        return prts

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []

        proc_data = Processo.get_processo_by_id(self.active_conn, self.prc_id)
        if proc_data[0]['prc_valor_causa'] is not None and not self.completo:
            return []

        divs = self.driver.find_elements_by_xpath('//*[@id="campoDetalhesProcesso"]/div/div')
        comarca = ''
        numero = ''
        # for div in divs:
        #     legend = div.find_elements_by_tag_name('legend')
        #
        #     if not legend:
        #         continue
        #
        #     if legend[0].text.find('Número Antigo') > -1:
        #         span = div.find_element_by_tag_name('span').text
        #         barra = span.find('/')
        #         comarca = span[:barra].replace('.','').replace('-','')
        #         numero = span[barra+1:].replace('.','').replace('-','')

        # if comarca == '':
        url = self.driver.execute_script('return window.location')
        url = url['href'].split('/')
        comarca = url[-1]
        numero = url[-2]

        btns = self.driver.find_elements_by_xpath('//*[@id="container-principal"]/ppe-detalhes-processo/ppe-acoes-detalhes-processo/tjrs-header/nav/div[2]/div/button/i')
        for btn in btns:
            cls = btn.get_attribute('class')
            if cls.find('search') > -1:
                btn.click()
                break
        # self.driver.find_element_by_xpath('//*[@id="container-principal"]/ppe-detalhes-processo/ppe-acoes-detalhes-processo/tjrs-header/nav/div[2]/div/button[3]/span').click()

        # self.driver.execute_script("window.open('" + href + "', '_blank')")
        self.alterna_janela()
        outras_info = self.driver.find_elements_by_partial_link_text('Ver Outras Informações')
        ver_todas = self.driver.find_elements_by_partial_link_text('Ver todas')

        inicio = time.time()
        while len(outras_info) == 0 and len(ver_todas) == 0:
            if (time.time() - inicio) >= 40:
                raise MildException("Erro ao preencher captcha", self.uf, self.plataforma, self.prc_id, False)
            outras_info = self.driver.find_elements_by_partial_link_text('Ver Outras Informações')
            ver_todas = self.driver.find_elements_by_partial_link_text('Ver todas')

        if len(outras_info) > 0:
            self.driver.find_element_by_partial_link_text('Ver Outras Informações').click()
        else:
            href = 'https://consulta.tjrs.jus.br/consulta-processual/processo/partes?numeroProcesso='+ numero +'&codComarca='+ comarca
            self.driver.get(href)

        # self.driver.get(href)
        # menu = self.driver.find_elements_by_xpath('/html/body/app-root/app-processo-root/app-menu-processo/mat-toolbar/mat-toolbar-row/button[1]/span/span')
        # while len(menu) == 0:
        #     menu = self.driver.find_elements_by_xpath('/html/body/app-root/app-processo-root/app-menu-processo/mat-toolbar/mat-toolbar-row/button[1]/span/span')
        inicio = time.time()
        while True:
            if (time.time() - inicio) >= 120:
                raise MildException("Erro ao preencher captcha", self.uf, self.plataforma, self.prc_id, False)
            try:
                self.driver.find_element_by_xpath('/html/body/app-root/app-processo-root/app-menu-processo/mat-toolbar/mat-toolbar-row/button[1]/span/span').click()
                break
            except:
                pass
        # aguarda_presenca_elemento(self.driver, '//*[@id="mat-menu-panel-0"]/div/button[2]', aguarda_visibilidade=True)
        while True:
            try:
                self.driver.find_element_by_xpath('//*[@id="mat-menu-panel-0"]/div/button[2]').click()
                break
            except:
                pass


        capturar = True
        # if not aguarda_presenca_elemento(self.driver, '/html/body/app-root/app-processo-root/div/app-partes/div/table/tbody/tr[1]/td[3]'):
        #     # self.driver.execute_script("window.open('" + href + "', '_self')")
        #     self.driver.get(href)

        if not aguarda_presenca_elemento(self.driver, '/html/body/app-root/app-processo-root/div/app-partes/div/table/tbody/tr[1]/td[3]'):
            err = self.driver.find_element_by_xpath('/html/body/app-root/app-processo-root/div/app-partes/mat-card/mat-card-content')
            if err:
                # capturar = False
                if err.text.find('identificador inválido') > -1:
                    capturar = False
                elif err.text.find('Serviço indisponível') > -1:
                    return []
                else:
                    raise MildException("Erro ao abrir página de partes", self.uf, self.plataforma, self.prc_id)

        if capturar:
            aguarda_presenca_elemento(self.driver, '/html/body/app-root/app-processo-root/div/app-partes/div/table/tbody/tr[1]/td[3]')
            table = self.driver.find_elements_by_xpath('/html/body/app-root/app-processo-root/div/app-partes/div/table/tbody/tr')

            nomes = []
            for tr in table:
                tipo = tr.find_elements_by_xpath('td[2]')
                if len(tipo) == 0:
                    continue
                tipo = tipo[0].text
                ps = tr.find_elements_by_xpath('td[3]/p')
                if len(ps) == 0:
                    continue

                if find_string(tipo,self.titulo_partes['ignorar']):
                    continue
                if find_string(tipo,self.titulo_partes['terceiro']):
                    continue

                polo = ''
                if find_string(tipo,self.titulo_partes['ativo']):
                    polo = 'Polo Ativo'
                if find_string(tipo,self.titulo_partes['passivo']):
                    polo = 'Polo Passivo'

                if polo == '':
                    raise MildException("polo vazio "+tipo, self.uf, self.plataforma, self.prc_id)

                for p in ps:
                    prr_nome = p.text
                    f = prr_nome.find(' - OAB:')
                    prr_oab = prr_nome[f+7:].strip()
                    prr_nome = prr_nome[:f].strip()
                    if prr_nome in nomes:
                        continue
                    nomes.append(prr_nome)
                    resps.append({'prr_nome': prr_nome, 'prr_oab': prr_oab, 'prr_cargo': 'Advogado', 'prr_parte': polo})


        # self.driver.get('https://consulta.tjrs.jus.br/consulta-processual/processo/informacoes/outras-informacoes?numeroProcesso='+numero+'&codComarca=' + comarca + '&perfil=0')
        self.driver.find_element_by_xpath('/html/body/app-root/app-processo-root/app-menu-processo/mat-toolbar/mat-toolbar-row/button[4]').click()
        aguarda_presenca_elemento(self.driver, '//*[@id="mat-menu-panel-3"]/div/button[3]', aguarda_visibilidade=True)
        inicio = time.time()
        while True:
            if (time.time() - inicio) >= 20:
                self.driver.get('https://consulta.tjrs.jus.br/consulta-processual/processo/informacoes/outras-informacoes?numeroProcesso=' + numero + '&codComarca=' + comarca + '&perfil=0')
                break
            try:
                self.driver.find_element_by_xpath('//*[@id="mat-menu-panel-3"]/div/button[3]').click()
                break
            except:
                pass

        if not aguarda_presenca_elemento(self.driver, '//*[@id="htmlData"]/div/div/mat-card/mat-card-content/span[1]'):
            mat = self.driver.find_element_by_xpath('//*[@id="htmlData"]/div/mat-card')
            if mat:
                if mat.text.find('Cannot obtain connection') > -1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    return []
            self.driver.get('https://consulta.tjrs.jus.br/consulta-processual/processo/informacoes/outras-informacoes?numeroProcesso='+numero+'&codComarca=' + comarca + '&perfil=0')
            if not aguarda_presenca_elemento(self.driver, '//*[@id="htmlData"]/div/div/mat-card/mat-card-content/span[1]', tempo=60):
                raise MildException("Erro ao abrir página de dados", self.uf, self.plataforma, self.prc_id)

        if aguarda_presenca_elemento(self.driver, '/html/body/app-root/app-processo-root/div/app-cabecalho-proc/div[2]/div[2]/span'):
            txt = self.driver.find_element_by_xpath('/html/body/app-root/app-processo-root/div/app-cabecalho-proc/div[2]/div[2]/span').text
            dr = txt.find('Dra.')
            if dr == -1:
                dr = txt.find('Dr.')

            if dr > -1:
                nome = txt[dr:]
                p1 = nome.find(' ')
                if p1 > -1:
                    nome = nome[p1:]
                p2 = nome.find('(')
                if p2 > -1:
                    nome = nome[:p2]
                resps.append({'prr_nome': nome.strip(), 'prr_oab': '', 'prr_cargo': 'Juiz', 'prr_parte': ''})

        return resps

     # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        '''
        :param str status_atual: Status atual
        '''
        prc = {}

        html = self.driver.find_element_by_xpath('//*[@id="htmlData"]/div/div/mat-card/mat-card-content')
        if html:
            html = html.get_attribute('innerHTML')
            dds = html.split('<br')

            for d in dds:
                rs = d.find('R$')
                if rs > -1:
                    valor = d[rs:]
                    prc['prc_valor_causa'] = valor.strip()
                    break

        wh = self.driver.window_handles
        if len(wh) > 1:
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

        # LOCALIZA STATUS DO PROCESSO
        prc['prc_status'] = get_status(self.movs, status_atual)

        prc_numero2 = self.driver.find_element_by_xpath('//*[@id="campoDetalhesProcesso"]/div[1]/div[1]/span').text
        prc['prc_numero2'] = prc_numero2

        classe = self.driver.find_element_by_xpath('//*[@id="campoDetalhesProcesso"]/div[3]/div[1]/span').text
        ex = classe.split('/')
        prc['prc_classe'] = ex[0].strip()
        prc['prc_assunto'] = ex[1].strip()

        prc['prc_serventia'] = self.driver.find_element_by_xpath('//*[@id="campoDetalhesProcesso"]/div[2]/div/span').text
        prc['prc_comarca2'] = localiza_comarca(prc['prc_serventia'], self.uf)

        prc_distribuicao = self.driver.find_element_by_xpath('//*[@id="campoDetalhesProcesso"]/div[5]/div[1]/span').text
        prc['prc_distribuicao'] = datetime.strptime(prc_distribuicao, '%d/%m/%Y')
        prc['prc_migrado'] = self.proc_data['prc_migrado']

        return prc

    # AGUARDA ATÉ QUE A ANIMAÇÃO DE LOADING ESTEJA OCULTA
    def wait(self, tempo=10, id='loadingBar'):
        if self.driver.find_element_by_id(id):
            wait = WebDriverWait(self.driver, tempo)
            try:
                wait.until(EC.invisibility_of_element((By.ID, id)))
            except TimeoutException:
                raise MildException("Loading Timeout", self.uf, self.plataforma, self.prc_id, False)

        return True

    # FECHA A JANELA DO PROCESSO ABERTO ATUALMENTE
    def fecha_processo(self):
        wh = self.driver.window_handles
        while len(wh) > 1:
            try:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.close()
            except:
                pass
            wh = self.driver.window_handles
        self.driver.switch_to.window(self.driver.window_handles[0])

    # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS
    def download(self, prc_id, arquivos_base, pendentes, target_dir):
        # return []
        # print(arquivos_base)
        # print('pen', pendentes)
        arquivos = []

        if self.tipo == 1:
            self.wait()
            self.driver.find_element_by_xpath('//*[@id="processos-grid"]/div/div/table/tbody/tr[1]/td[6]').click()
            if not aguarda_presenca_elemento(self.driver, '//*[@id="campoDetalhesProcesso"]/div[1]/div/span'):
                raise MildException("Erro ao abrir processo", self.uf, self.plataforma, self.prc_id, False)
            self.wait()

        di = 0
        achei = False
        btns = self.driver.find_elements_by_xpath('/html/body/app-root/div/ppe-detalhes-processo/div')
        for btn in btns:
            di += 1
            titulo = btn.text.upper()
            if titulo.find('DOCUMENTOS DOS AUTOS') > -1:
                btn.location_once_scrolled_into_view
                pos = self.driver.execute_script('return document.documentElement.scrollTop')
                self.driver.execute_script("window.scrollTo(0,"+str(pos-200)+");")
                btn.click()
                achei = True
                break

        if not achei:
            return arquivos

        if not aguarda_presenca_elemento(self.driver, '//*[@id="container-principal"]/ppe-detalhes-processo/div['+str(di)+']/ppe-collapsible/div[2]/ppe-detalhes-processo-documentos/div[2]/p-datatable/div/div[1]/div/div[2]/div/table/tbody', aguarda_visibilidade=True):
            return []
            raise MildException("Erro ao carregar tabela de arquivos", self.uf, self.plataforma, self.prc_id, False)

        movimentos = self.driver.find_elements_by_xpath('//*[@id="container-principal"]/ppe-detalhes-processo/div['+str(di)+']/ppe-collapsible/div[2]/ppe-detalhes-processo-documentos/div[2]/p-datatable/div/div[1]/div/div[2]/div/table/tbody/tr')
        movimentos.reverse()
        existe = False
        i = 0
        for mov in movimentos:
            i += 1

            if existe and len(pendentes) == 0:
                break

            arq = {}
            pra_id_tj = mov.find_element_by_xpath('td[5]').text
            pra_descricao = mov.find_element_by_xpath('td[2]').text + ' - ' + mov.find_element_by_xpath('td[3]').text
            dia = mov.find_element_by_xpath('td[6]').text
            mov.location_once_scrolled_into_view
            pos = self.driver.execute_script('return document.documentElement.scrollTop')
            self.driver.execute_script("window.scrollTo(0," + str(pos - 200) + ");")
            arq['pra_id_tj'] = pra_id_tj
            arq['pra_tentativas'] = None
            arq['pra_prc_id'] = prc_id
            arq['pra_grau'] = self.grau
            arq['pra_plt_id'] = self.plataforma
            arq['pra_descricao'] = pra_descricao
            arq['pra_data'] = datetime.strptime(dia, '%d/%m/%Y %H:%M:%S')
            arq['pra_erro'] = True
            arq['pra_excluido'] = False
            arq['pra_original'] = None
            arq['pra_arquivo'] = None

            limpar_pasta(self.pasta_download)

            if len(pendentes) > 0:
                for pen in pendentes[:]:
                    if pen['pra_id_tj'] == arq['pra_id_tj']:
                        arq['pra_id'] = pen['pra_id']
                        arq['pra_tentativas'] = pen['pra_tentativas']
                        pendentes.remove(pen)

            if 'pra_id' not in arq:
                for arb in arquivos_base:
                    if arq['pra_id_tj'] == arb['pra_id_tj']:
                        existe = True
                        break

                if existe:
                    if len(pendentes) == 0:
                        break
                    continue

            if self.tipo != 2:
                ban = mov.find_elements_by_class_name('fa-ban')
                if len(ban) > 0:
                    arq['pra_erro'] = True
                    # arq['pra_excluido'] = True
                else:
                    try:
                        mov.find_element_by_xpath('td[1]/span/a').click()
                    except:
                        raise MildException("Erro ao clicar no download", self.uf, self.plataforma, self.prc_id, False)
                    self.wait(tempo=30)
                    aguarda_presenca_elemento(self.driver, 'toasty', tipo='ID', tempo=0.5, aguarda_visibilidade=True)
                    toast = self.driver.find_element_by_id('toasty')
                    if toast and toast.text.find('Não foi possível recuperar o documento') > -1:
                        self.driver.find_element_by_xpath('//*[@id="toasty"]/gx-toast/div/div').click()
                        print('Não foi possível recuperar o documento')
                        arq['pra_erro'] = True
                    else:
                        arq['pra_erro'] = False if aguarda_download(self.pasta_download, 1) else True

                    toast = self.driver.find_element_by_id('toasty')
                    if toast and toast.text.find('Não foi possível recuperar o documento') > -1:
                        self.driver.find_element_by_xpath('//*[@id="toasty"]/gx-toast/div/div').click()

                if not arq['pra_excluido']:
                    if not arq['pra_erro']:
                        file_names = os.listdir(self.pasta_download)
                        arq['pra_original'] = file_names[0]
                        pra_arquivo = trata_arquivo(file_names[0], self.pasta_download, target_dir)
                        arq['pra_arquivo'] = pra_arquivo
                    elif arq['pra_erro'] and self.tipo != 2:
                        arq['pra_original'] = None
                        arq['pra_arquivo'] = None
                        arq['pra_tentativas'] = 1 if arq['pra_tentativas'] is None else arq['pra_tentativas'] + 1
                        print('erro download')
                        # time.sleep(9999)
                        # raise MildException('erro download ' + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)

            arq['pra_data_insert'] = datetime.now()
            # print(arq)
            arquivos.append(arq)

        arquivos.reverse()
        return arquivos
