from Config.helpers import *
from Controllers.Tribunais.primeiro_grau import *
from selenium.webdriver.common.keys import *
from Models.processoModel import *

import sys, time, shutil

# CLASSE DA VARREDURA DO EPROC. HERDA OS METODOS DA CLASSE PLATAFORMA
class Eproc(PrimeiroGrau):

    def __init__(self):
        super().__init__()
        self.plataforma = 7
        self.movs = []
        self.active_window = 0
        self.handles = []
        self.diferenciar_id_download_2g = True

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''
        if not aguarda_presenca_elemento(self.driver, 'sbmEntrar', tipo='ID'):
            return False

        self.handles = [self.driver.current_window_handle]
        if usuario is None:
            self.driver.find_element_by_id('lnkEntrarCert').click()
        else:
            self.driver.find_element_by_id('txtUsuario').send_keys(usuario)
            self.driver.find_element_by_id('pwdSenha').send_keys(senha)
            self.driver.find_element_by_xpath('//*[@id="frmLogin"]/div/div[3]/button').click()

        try_click(self.driver, 'tr1', tipo='ID')

        # if self.driver.find_element_by_id('txtCaptcha'):
        #     self.driver.find_element_by_id('txtUsuario').send_keys(usuario)
        #     self.driver.find_element_by_id('pwdSenha').send_keys(senha)
        #     while True:
        #         txt_capcha = self.driver.find_element_by_id('txtCaptcha').get_attribute('value')
        #         time.sleep(1)
        #         # Aguarda a digitação dos 5 caracteres
        #         if len(txt_capcha) != 6:
        #             continue
        #
        #         break
        #     self.driver.find_element_by_xpath('//*[@id="frmLogin"]/div/div[3]/button').click()

        if not self.reiniciar_navegador:
            if not aguarda_presenca_elemento(self.driver, 'btnProfile', tipo='ID', tempo=300):
                return False
        else:
            if not aguarda_presenca_elemento(self.driver, 'btnProfile', tipo='ID'):
                return False

        return True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''

        if self.grau == 2:
            wh = self.driver.window_handles
            if len(wh) == 1:
                raise CriticalException("Somente uma janela de Busca localizada", self.uf, self.plataforma, self.prc_id, False)

        inicio = time.time()
        while True:
            if time.time() - inicio > 30:
                raise CriticalException("Erro ao limpar Campo de busca", self.uf, self.plataforma, self.prc_id, False)
            self.wait()
            self.process_main_child = foca_janela(self.process_main_child)
            campo_busca = localiza_elementos(self.driver, ('//*[@id="navbar"]/div/div[3]/div[4]/form/input[1]','//*[@id="frmProcessoPesquisaRapida"]/input[1]','//*[@id="navbar"]/div/div[3]/div[3]/form/input[1]',))
            if not campo_busca:
                self.driver.refresh()
                raise CriticalException("Campo de busca não localizado", self.uf, self.plataforma, self.prc_id, False)

            try:
                campo_busca.clear()
                break
            except:
                self.driver.refresh()
                time.sleep(3)

        # chk = self.driver.find_element_by_xpath('//*[@id="divChkExibirBaixados"]/dl/dd/input')
        # if chk:
        #     chk.click()

        try:
            campo_busca.send_keys(numero_busca)
            campo_busca.send_keys(Keys.ENTER)
        except StaleElementReferenceException:
            raise MildException("Página atualizada", self.uf, self.plataforma, self.prc_id, False)

        if aguarda_alerta(self.driver, 0.2, False, False):
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            self.driver.switch_to.alert.accept()
            if alert_text.find('processo inválido') > -1:
                return False

        painel = self.driver.find_element_by_xpath('//*[@id="divInfraBarraLocalizacao"]/div/h4')
        if painel:
            if painel.text.find('Painel do Advogado') > -1:
                raise MildException("Erro na busca (voltou para o painel)", self.uf, self.plataforma, self.prc_id, False)

        self.wait()

        divInfraCaptcha = self.driver.find_element_by_id('divInfraCaptcha')
        if divInfraCaptcha and divInfraCaptcha.is_displayed():
            raise CriticalException("Captcha Detectado", self.uf, self.plataforma, self.prc_id, False)

        if self.driver.find_element_by_id('txtCaptcha'):
            if self.driver.find_element_by_id('txtCaptcha').is_displayed():
                raise CriticalException("Captcha Detectado", self.uf, self.plataforma, self.prc_id, False)

        div_erro = self.driver.find_element_by_id('divInfraExcecao')
        if div_erro:
            if div_erro.text.upper().find('NÃO ENCONTRADO') > -1:
                return False
        else:
            self.wait()
            if self.driver.find_element_by_id('numNrProcesso'):
                if not self.driver.find_element_by_id('txtNumProcesso'):
                  return False

        return True

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        aguarda_presenca_elemento(self.driver,'txtNumProcesso', tipo='ID')
        el = self.driver.find_element_by_id('txtNumProcesso')
        if el:
            numero_site = ajusta_numero(el.text)
            if numero_busca == numero_site:
                return True

        # foca_janela(self.process_children)
        raise MildException("Número CNJ Diferente", self.uf, self.plataforma, self.prc_id)

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        div_erro = self.driver.find_element_by_id('divInfraExcecao')
        if div_erro:
            if div_erro.text.upper().find('SIGILO') > -1:
                return True

        self.confere_cnj(numero_busca)

        if check_text(self.driver, 'lblAvisoTopolabel', 'Segredo', tipo='ID'):
            trs = self.driver.find_elements_by_xpath('//*[@id="tblEventos"]/tbody/tr')
            if len(trs) == 0:
                return True

        return False

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        self.wait(10)
        if not aguarda_presenca_elemento(self.driver, '//*[@id="tblEventos"]/tbody/tr[1]/td[2]', tempo=10):
            raise MildException("Erro ao capturar data", self.uf, self.plataforma, self.prc_id)

        dia = self.driver.find_element_by_xpath('//*[@id="tblEventos"]/tbody/tr[1]/td[2]').text

        data_tj = datetime.strptime(dia.strip(), '%d/%m/%Y %H:%M:%S')
        if ultima_data == data_tj:
            return True

        return False

    # CAPTURA ACOMPANHAMENTOS DO PROCESSO
    def acompanhamentos(self, proc_data, completo, base):
        '''
        :param datetime Última movimentação registrada na base
        :param bool Realiza a captura completa das movimentações
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        ultima_mov = proc_data['cadastro']
        prc_id = proc_data['prc_id']
        rec_id = proc_data['rec_id'] if 'rec_id' in proc_data else None

        self.movs = []
        movs = []
        lista = Acompanhamento.lista_movs(base, prc_id, self.plataforma, acp_grau=self.grau, rec_id=rec_id)

        if self.grau == 1:
            self.insert_recursos(base, proc_data)

        # if completo:
            # if len(self.driver.find_elements_by_xpath('//*[@id="tblEventos"]/tbody/tr')) > 9:
        if try_click(self.driver, 'Acesso íntegra do processo', tipo='LINK_TEXT'):
            try:
                self.driver.switch_to.alert.accept()
            except NoAlertPresentException:
                pass
            time.sleep(0.5)
            if self.driver.find_element_by_id('ifrSubFrm'):
                self.driver.switch_to.frame(self.driver.find_element_by_id('ifrSubFrm'))
                if self.driver.find_element_by_id('divInfraCaptcha'):
                    self.driver.find_element_by_xpath('//*[@id="frmVistaProcesso"]/div/div[3]/button[2]').click()
                else:
                    self.driver.find_element_by_xpath('//*[@id="frmVistaProcesso"]/div/div[3]/button[1]').click()
                self.driver.switch_to.default_content()

            # aguarda_presenca_elemento(self.driver, '//*[@id="tblEventos"]/tbody/tr')
            aguarda_alerta(self.driver, 5)

            div_erro = self.driver.find_element_by_id('divInfraExcecao')
            if div_erro:
                if div_erro.text.upper().find('OUTRO GRAU DE JURISDIÇÃO') > -1:
                    self.driver.execute_script("window.history.go(-1)")


        if try_click(self.driver, '//*[@id="infraAjaxCarregarPaginasNormal"]/a[2]'):
            time.sleep(1)

        try:
            movimentos = self.driver.find_elements_by_xpath('//*[@id="tblEventos"]/tbody/tr')
        except UnexpectedAlertPresentException:
            self.driver.switch_to.alert.accept()
            movimentos = self.driver.find_elements_by_xpath('//*[@id="tblEventos"]/tbody/tr')

        if len(movimentos) == 0:
            raise MildException("Erro ao capturar movimentações", self.uf, self.plataforma, self.prc_id, False)

        i = 0
        for mov in movimentos:
            i += 1
            capturar = True
            acp_tipo = mov.find_element_by_xpath('td[1]').text.strip()
            acp_cadastro = mov.find_element_by_xpath('td[2]').text
            acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y %H:%M:%S')

            achei = False
            for l in lista:
                if acp_cadastro == l['acp_cadastro'] and acp_tipo.strip() == l['acp_tipo'].strip():
                    achei = True
                    break

            if achei:
                capturar = False
                if not completo and i >= 10:
                    break

            # if acp_cadastro == ultima_mov:
            #     capturar = False
            #     if not completo and i >= 10:
            #         break

            acp_esp = mov.find_element_by_xpath('td[3]').text
            acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp, 'acp_tipo': acp_tipo}
            if capturar:
                movs.append(acp)

            self.movs.append({**acp, 'novo': capturar})

        return movs

    # LOCALIZA RECURSOS E INSERE NA BASE
    def insert_recursos(self, base, proc):
        rels = self.driver.find_elements_by_xpath('//*[@id="tableRelacionado"]/tbody/tr')
        achei = False
        if len(rels) > 0:
            for rel in rels:
                td3 = rel.find_elements_by_xpath('td[3]')

                if len(td3) == 0:
                    continue

                tipo_rel = rel.find_element_by_xpath('td[3]').text
                tipo_rel += ' ' + rel.find_element_by_xpath('td[5]').text
                rec_numero = rel.find_element_by_xpath('td[1]').text.strip()
                f = rec_numero.find('/')
                if f > -1:
                    rec_numero = rec_numero[:f].strip()

                if find_string(tipo_rel, ('Recurso', '2o. grau', '2º grau', 'Apelação', 'Dependente', 'Agravo')):
                    if find_string(tipo_rel, ('Dependente', )):
                        if find_string(tipo_rel, ('PROCEDIMENTO COMUM CÍVEL','PROCEDIMENTO DO JUIZADO E')):
                            print('Inserindo novo processo')
                            self.insere_novo_processo(rec_numero)
                            continue

                    rec_url = rel.find_element_by_xpath('td[1]/font/a').get_attribute('href')
                    if rec_url.find('site_php') > -1:
                        continue

                    result = Recurso.select(base, proc['prc_id'], rec_numero=rec_numero, rec_plt_id=7)
                    if len(result) == 0:
                        # if not Processo.processo_existe(self.conn_atual, rec_numero):
                        Recurso.insert(base, {'rec_prc_id': proc['prc_id'], 'rec_numero': rec_numero, 'rec_plt_id': self.plataforma})
                        achei = True
                    continue

                rec_limpo = rec_numero.replace('-','').replace('.','')
                if len(rec_limpo) < 22:
                    self.insere_novo_processo(rec_numero)

        return achei

    # CAPTURA AUDIENCIAS DO PROCESSO
    def audiencias(self):
        adcs = []
        for mov in self.movs:
            if not self.completo and not mov['novo']:
                break

            esp = mov['acp_esp'].upper().strip()

            if esp.find('AUDIÊNCIA') != 0:
                continue

            aud = localiza_audiencia(esp)
            if not aud:
                continue

            erro = ''
            if 'prp_status' not in aud:
                erro = 'Status '
            if 'prp_tipo' not in aud:
                erro = 'Tipo '

            if erro != '':
                raise MildException("Audiência - "+erro+" não localizado: "+esp, self.uf, self.plataforma, self.prc_id)

            serventia = None
            p = esp.find('LOCAL')
            if p > -1:
                serventia = mov['acp_esp'][p+5:].strip()
                p = serventia.find('-')
                if p > -1:
                    serventia = serventia[:p].strip()

            aud['prp_serventia'] = serventia
            aud['data_mov'] = mov['acp_cadastro']
            adcs.append(aud)

        return adcs

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo': [], 'passivo': []}

        carregarOutrosA = self.driver.find_element_by_xpath('//*[@id="carregarOutrosA"]/a')
        ambos = False
        if carregarOutrosA:
            trs = self.driver.find_elements_by_xpath('//*[@id="tblPartesERepresentantes"]/tbody/tr')

            self.driver.execute_script("window.scrollTo( 0, 0 )")
            script = self.driver.find_element_by_xpath('//*[@id="carregarOutrosA"]/a').get_attribute('href')
            self.driver.execute_script(script)
            # carregarOutrosA.click()
            wait = WebDriverWait(self.driver, 5)
            try:
                wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="tblPartesERepresentantes"]/tbody/tr['+str(len(trs)+1)+']')))
                ambos = True
            except TimeoutException:
                raise MildException('erro ao carregar outras partes', self.uf, self.plataforma, self.prc_id)
                pass

            carregarOutrosR = self.driver.find_element_by_xpath('//*[@id="carregarOutrosR"]/a')
            if carregarOutrosR:
                trs = self.driver.find_elements_by_xpath('//*[@id="tblPartesERepresentantes"]/tbody/tr')

                self.driver.execute_script("window.scrollTo( 0, 0 )")
                script = self.driver.find_element_by_xpath('//*[@id="carregarOutrosR"]/a').get_attribute('href')
                self.driver.execute_script(script)
                wait = WebDriverWait(self.driver, 5)
                if ambos:
                    time.sleep(1)
                else:
                    try:
                        wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="tblPartesERepresentantes"]/tbody/tr[' + str(len(trs) + 1) + ']')))
                    except TimeoutException:
                        raise MildException('erro ao carregar outras partes', self.uf, self.plataforma, self.prc_id)
                        pass

            # self.driver.execute_script("window.scrollTo( 0, 0 )")
            # if try_click(self.driver, '//*[@id="tblPartesERepresentantes"]/tbody/tr[2]/td[1]/span[3]/a'):
            #     wait = WebDriverWait(self.driver, 1)
            #     try:
            #         wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="tblPartesERepresentantes"]/tbody/tr[3]')))
            #     except TimeoutException:
            #         pass
            #
            # if try_click(self.driver, '//*[@id="tblPartesERepresentantes"]/tbody/tr[2]/td[2]/span[3]/a'):
            #     wait = WebDriverWait(self.driver, 1)
            #     try:
            #         wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="tblPartesERepresentantes"]/tbody/tr[3]')))
            #     except TimeoutException:
            #         pass

        tipo_parte = self.driver.find_element_by_xpath('//*[@id="tblPartesERepresentantes"]/tbody/tr[1]/th[1]').text
        polo_td1 = ''
        polo_td2 = ''
        if tipo_parte == 'AUTOR' or tipo_parte == 'REQUERENTE' or tipo_parte == 'EXEQUENTE' or tipo_parte == 'AGRAVANTE':
            polo_td1 = 'ativo'
            polo_td2 = 'passivo'


        i = 0
        trs = self.driver.find_elements_by_xpath('//*[@id="tblPartesERepresentantes"]/tbody/tr')
        if len(trs) == 1:
            raise MildException('erro ao carregar tabela de partes', self.uf, self.plataforma, self.prc_id)

        for tr in trs:
            ctd2 = tr.find_elements_by_xpath('td[2]')
            if len(ctd2) == 0:
                continue
            j = 1
            tds = tr.find_elements_by_xpath('td')
            for td in tds:
                nome = td.find_elements_by_class_name('infraNomeParte')
                if len(nome) > 0:
                    nome = nome[0]
                    prt_nome = nome.text
                    if prt_nome == 'OS MESMOS':
                        continue

                    txt_td = td.text
                    if find_string(txt_td, ('(AUTOR)','REQUERENTE','EXEQUENTE','AGRAVANTE')):
                        polo_td = 'ativo'
                    elif find_string(txt_td, ('(RÉU)', 'REQUERIDO','EXECUTADO','AGRAVADO')):
                        polo_td = 'passivo'
                    else:
                        if polo_td1 != '' and polo_td2 != '':
                            polo_td = polo_td1 if j == 1 else polo_td2
                        else:
                            continue

                    prt_cpf_cnpj = 'Não Informado'
                    id_cpf = 'spnCpfParteAutor' if j == 1 else 'spnCpfParteReu'
                    cpf = td.find_elements_by_id(id_cpf+str(i))
                    if len(cpf) > 0:
                        prt_cpf_cnpj = cpf[0].text
                    partes[polo_td].append({'prt_nome': prt_nome, 'prt_cpf_cnpj': prt_cpf_cnpj})

                j += 1

            i += 1

        # print(partes)
        # if len(partes['ativo']) == 0 or len(partes['passivo']) == 0:
        #     time.sleep(9999)
        #     print('parte em branco', partes)
        #     raise MildException('parte em branco', self.uf, self.plataforma, self.prc_id)
        # time.sleep(9999)
        return partes

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []

        # CAPTURA NOME JUIZ
        magistrado = self.driver.find_element_by_id('txtMagistrado').text
        resps.append({'prr_nome': magistrado.strip(), 'prr_oab': '', 'prr_cargo': 'Juiz', 'prr_parte': ''})


        tipo_parte = self.driver.find_element_by_xpath('//*[@id="tblPartesERepresentantes"]/tbody/tr[1]/th[1]').text
        polo_td1 = ''
        polo_td2 = ''
        if tipo_parte == 'AUTOR' or tipo_parte == 'REQUERENTE' or tipo_parte == 'EXEQUENTE' or tipo_parte == 'AGRAVANTE':
            polo_td1 = 'Polo Ativo'
            polo_td2 = 'Polo Passivo'

        trs = self.driver.find_elements_by_xpath('//*[@id="tblPartesERepresentantes"]/tbody/tr')
        for i in range(1,3):
            for tr in trs:
                ctd2 = tr.find_elements_by_xpath('td[2]')
                if len(ctd2) == 0:
                    continue
                td = tr.find_element_by_xpath('td['+str(i)+']')
                polo = ''
                txt_td = td.text
                # print('td',txt_td,polo_td1,polo_td2)
                if find_string(txt_td, ('(AUTOR)', 'REQUERENTE', 'EXEQUENTE','AGRAVANTE')):
                    polo = 'ativo'
                elif find_string(txt_td, ('(RÉU)', 'REQUERIDO', 'EXECUTADO','AGRAVADO')):
                    polo = 'passivo'
                else:
                    if polo_td1 != '' and polo_td2 != '':
                        polo = polo_td1 if i == 1 else polo_td2
                    else:
                        continue

                html = td.get_attribute('innerHTML')
                prts = html.split('<br>')
                for prt in prts:
                    if prt.find('<a') == -1:
                        continue

                    nomes = prt.split('<a')
                    if nomes[0].find('spnNomeParteReu') > -1 or nomes[0].find('spnCpfParteAutor') > -1:
                        continue

                    nome = nomes[0].replace('&nbsp;','').replace('\r','').replace('\n','')
                    nome = strip_html_tags(nome)
                    if nome == '':
                        continue

                    oab = '<a'+nomes[1]
                    oab = oab.replace('&nbsp;','').replace('\r','').replace('\n','')
                    oab = strip_html_tags(oab)
                    p = oab.find('(')
                    if p > -1:
                        oab = oab[:p-1].strip()

                    nome = nome.replace(oab,'')
                    nome = nome.replace('(DPE)', '')
                    resps.append({'prr_nome': nome.strip(), 'prr_oab': oab, 'prr_cargo': 'Advogado', 'prr_parte': polo})

        return resps

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        prc = {}

        if status_atual == 'Segredo de Justiça':
            status_atual = 'Ativo'

        prc['prc_status'] = get_status(self.movs, status_atual)

        serventia = self.driver.find_element_by_id('txtOrgaoJulgadorJEF')
        if serventia:
            prc['prc_serventia'] = serventia.text
        else:
            prc['prc_serventia'] = self.driver.find_element_by_id('txtOrgaoJulgador').text

        prc['prc_comarca2'] = localiza_comarca(prc['prc_serventia'], self.uf)
        prc['prc_numero2'] = self.driver.find_element_by_id('txtNumProcesso').text
        prc['prc_classe'] = self.driver.find_element_by_id('txtClasse').text
        prc_distribuicao = self.driver.find_element_by_id('txtAutuacao').text
        prc['prc_distribuicao'] = datetime.strptime(prc_distribuicao, '%d/%m/%Y %H:%M:%S')

        # EXIBE TABELA DE INFORMAÇÕES ADICIONAIS
        try:
            self.driver.execute_script("infraAbrirFecharElementoHTML('conteudoInfAdicional', 'imgStatusInfAdicional');")
        except:
            self.driver.refresh()
            try:
                self.driver.execute_script("infraAbrirFecharElementoHTML('conteudoInfAdicional', 'imgStatusInfAdicional');")
            except:
                raise MildException("Erro ao abrir tabela de dados adicionais", self.uf, self.plataforma, self.prc_id)

        wait = WebDriverWait(self.driver, 1)
        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="conteudoInfAdicional"]/table/tbody/tr[1]')))
        except TimeoutException:
            pass

        trs = self.driver.find_elements_by_xpath('//*[@id="conteudoInfAdicional"]/table/tbody/tr')
        campos = {'Valor da Causa': 'prc_valor_causa', 'Prioridade': 'prc_prioridade','Nível de Sigilo': 'prc_segredo',}
        for tr in trs:
            i = 0
            tds = tr.find_elements_by_xpath('td')
            for td in tds:
                i += 1
                txt = td.text
                for c in campos:
                    if txt.find(c) > -1:
                        prc[campos[c]] = tds[i].text
                        break

        if 'prc_prioridade' in prc:
            prc['prc_prioridade'] = True if prc['prc_prioridade'] == 'Sim' else False

        if 'prc_segredo' in prc:
            prc['prc_segredo'] = False if prc['prc_segredo'].find('Sem Sigilo') > -1 else True

        # EXIBE TABELA DE ASSUNTOS
        self.driver.execute_script("infraAbrirFecharElementoHTML('conteudoAssuntos2', 'imgStatusAssunto');")
        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="conteudoAssuntos2"]/table/tbody/tr[2]')))
        except TimeoutException:
            pass

        trs = self.driver.find_elements_by_xpath('//*[@id="conteudoAssuntos2"]/table/tbody/tr/td[2]')
        prc_assunto = []
        for tr in trs:
            prc_assunto.append(tr.text)

        prc['prc_assunto'] = " | ".join(prc_assunto)

        return prc

    # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS
    def download(self, prc_id, arquivos_base, pendentes, pasta_intermediaria):
        arquivos = []
        total_arquivos = 0
        # SE FOR SOMENTE DOWNLOAD, ABRE O LINK DOS DOWNLOADS
        if self.tipo != 2:
            # if len(self.driver.find_elements_by_xpath('//*[@id="tblEventos"]/tbody/tr')) > 9:
            if try_click(self.driver, 'Acesso íntegra do processo', tipo='LINK_TEXT'):
                try:
                    self.driver.switch_to.alert.accept()
                except NoAlertPresentException:
                    pass
                time.sleep(0.5)
                if self.driver.find_element_by_id('ifrSubFrm'):
                    self.driver.switch_to.frame(self.driver.find_element_by_id('ifrSubFrm'))
                    if self.driver.find_element_by_id('divInfraCaptcha'):
                        self.driver.find_element_by_xpath('//*[@id="frmVistaProcesso"]/div/div[3]/button[2]').click()
                    else:
                        self.driver.find_element_by_xpath('//*[@id="frmVistaProcesso"]/div/div[3]/button[1]').click()
                    self.driver.switch_to.default_content()
        #     if try_click(self.driver, 'Acesso íntegra do processo', tipo='LINK_TEXT'):
        #         try:
        #             self.driver.switch_to.alert.accept()
        #         except NoAlertPresentException:
        #             pass
        #
        #         aguarda_alerta(self.driver, tempo=10)
        #         aguarda_presenca_elemento(self.driver, '//*[@id="tblEventos"]/tbody/tr')


        div_erro = self.driver.find_element_by_id('divInfraExcecao')
        if div_erro:
            if div_erro.text.upper().find('OUTRO GRAU DE JURISDIÇÃO') > -1:
                self.driver.execute_script("window.history.go(-1)")

        element = self.driver.find_element_by_id("fldAcoes")
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        try_click(self.driver, 'chkMostrarComDocumentos', tipo='ID')
        # self.driver.find_element_by_id('chkMostrarComDocumentos').click()

        aguarda_alerta(self.driver, tempo=0.2)
        wait = WebDriverWait(self.driver, 1)
        try:
            wait.until(EC.visibility_of_element_located((By.ID, 'carregarNovosEventos')))
        except TimeoutException:
            pass
        except UnexpectedAlertPresentException:
            self.driver.switch_to.alert.accept()

        wait = WebDriverWait(self.driver, 30)
        try:
            wait.until(EC.invisibility_of_element((By.ID, 'carregarNovosEventos')))
        except TimeoutException:
            raise MildException("Loading Timeout", self.uf, self.plataforma, self.prc_id, False)

        while True:
            movimentos = self.driver.find_elements_by_xpath('//*[@id="tblEventos"]/tbody/tr')
            existe = False
            for mov in movimentos:
                pra_id_tj = mov.find_element_by_xpath('td[1]').text.strip()
                # if int(pra_id_tj) > 10:
                #     continue
                if self.tipo != 2:
                    self.driver.execute_script("document.getElementById('trEvento" + pra_id_tj + "').scrollIntoView({behavior: 'auto', block: 'center', inline: 'center'});")
                txt_td5 = mov.find_element_by_xpath('td[5]').text
                if txt_td5.find('Evento não gerou documento') > -1:
                    continue

                links = mov.find_elements_by_xpath('td[5]/a')
                # if existe and len(pendentes) == 0:
                #     break

                for a in links:
                    existe = False
                    arq = {}
                    arq['pra_id_tj'] = pra_id_tj
                    arq['pra_original'] = a.text
                    arq['pra_tentativas'] = None
                    pra_data = mov.find_element_by_xpath('td[2]').text
                    arq['pra_data'] = datetime.strptime(pra_data, '%d/%m/%Y %H:%M:%S')

                    if arq['pra_original'].strip() == '':
                        continue

                    if len(pendentes) > 0:
                        for pen in pendentes[:]:
                            arq_ori_pen = pen['pra_original'].replace(' ','').replace('_','')
                            arq_ori_arq = arq['pra_original'].replace(' ','').replace('_','')
                            if pen['pra_id_tj'] == arq['pra_id_tj'] and arq_ori_pen.find(arq_ori_arq) > -1 and pen['pra_grau'] == self.grau and pen['pra_data'] == arq['pra_data']:
                                arq['pra_id'] = pen['pra_id']
                                arq['pra_tentativas'] = pen['pra_tentativas']
                                pendentes.remove(pen)
                                break
                    # print(pra_id_tj, arq['pra_id_tj'], arq['pra_original'])
                    if 'pra_id' not in arq:
                        for arb in arquivos_base:
                            arq_ori_arb = arb['pra_original'].replace(' ','').replace('_','')
                            arq_ori_arq = arq['pra_original'].replace(' ','').replace('_','')
                            if arq['pra_id_tj'] == arb['pra_id_tj'] and arq_ori_arb.find(arq_ori_arq) > -1 and arb['pra_grau'] == self.grau and arb['pra_data'] == arq['pra_data']:
                                # print('achei', self.rec_id, arb)
                                existe = True
                                # if self.grau == 2 and arb['pra_rec_id'] is None:
                                #     ProcessoArquivo.update(self.conn_atual,[{'pra_rec_id': self.rec_id, 'pra_id': arb['pra_id']},])

                                break

                        if existe:
                            # if len(pendentes) == 0:
                            #     break
                            continue

                    arq['pra_prc_id'] = prc_id
                    arq['pra_grau'] = self.grau
                    arq['pra_plt_id'] = self.plataforma
                    arq['pra_usuario'] = mov.find_element_by_xpath('td[4]').text
                    arq['pra_descricao'] = mov.find_element_by_xpath('td[3]').text
                    arq['pra_excluido'] = False

                    # SE NÃO FOR PARA FAZER DOWNLOAD, SALVA SOMENTE NA BASE, E MARCA COMO ERRO, PARA REALIZAR O DOWNLOAD POSTERIORMENTE
                    if self.tipo == 2:
                        arq['pra_erro'] = True
                    else:
                        ext = a.get_attribute('data-mimetype').upper()
                        # print(ext)
                        erro = False
                        click = True
                        try:
                            click = self.click_download(a, ext)
                        except:
                            erro = True

                        if not click:
                            arq['pra_erro'] = False
                            arq['pra_excluido'] = True
                            # arq['pra_original'] = None
                            arq['pra_arquivo'] = None
                        else:
                            result_download = False
                            if not erro:
                                result_download = aguarda_download(self.pasta_download, 1, tempo_nao_iniciado=60)
                            if not result_download:
                                print('Tentanto baixar novamente')
                                # wh = self.driver.window_handles
                                try:
                                    webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                                except:
                                    pass
                                self.fecha_download(ext)
                                time.sleep(5)
                                limpar_pasta(self.pasta_download)
                                self.click_download(a, ext)
                                result_download = aguarda_download(self.pasta_download, 1, tempo_nao_iniciado=60)

                            arq['pra_erro'] = not result_download
                            if self.tipo != 2 and arq['pra_erro']:
                                webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

                        self.fecha_download(ext)

                    if not arq['pra_erro']:
                        total_arquivos += 1
                        if not arq['pra_excluido']:
                            file_names = os.listdir(self.pasta_download)
                            # arq['pra_original'] = file_names[0]
                            pra_arquivo = trata_arquivo(file_names[0], self.pasta_download, pasta_intermediaria)
                            arq['pra_arquivo'] = pra_arquivo
                    elif self.tipo != 2:
                        arq['pra_original'] = None
                        arq['pra_arquivo'] = None
                        arq['pra_tentativas'] = 1 if arq['pra_tentativas'] is None else arq['pra_tentativas'] + 1
                        limpar_pasta(self.pasta_download)
                        print('erro download')
                        # time.sleep(9999)
                        raise MildException('erro download ' + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)

                    arq['pra_data_insert'] = datetime.now()
                    arquivos.append(arq)

            btn_prox = self.driver.find_element_by_id('proximaR')
            if not btn_prox:
                break

            if not btn_prox.is_displayed():
                break

            td_ant = self.driver.find_element_by_xpath('//*[@id="tblEventos"]/tbody/tr[1]/td[1]').text
            td_atual = td_ant
            self.driver.find_element_by_id('proximaR').click()

            inicio = time.time()
            while td_ant == td_atual:
                if time.time() - inicio > 35:
                    raise MildException("Erro ao trocar de página", self.uf, self.plataforma, self.prc_id)
                try:
                    td_atual = self.driver.find_element_by_xpath('//*[@id="tblEventos"]/tbody/tr[1]/td[1]').text
                except:
                    pass

        arquivos.reverse()
        return arquivos

    def click_download(self, link, ext):
        limpar_pasta(self.pasta_download)
        href = link.get_attribute('href')
        if ext == 'PDF':
            href = href.replace('acessar_documento','acessar_documento_implementacao')
        # self.driver.execute_script("arguments[0].setAttribute('href', '"+href2+"')", link)
        self.driver.execute_script("window.open('" + href + "', '_blank')")

        if ext == 'HTML':
            self.alterna_janela((self.grau), 1, not_in_guid=self.handles)
            self.driver.execute_script('setTimeout(function() { window.print(); }, 0);')
            # try_click(self.driver, 'btnImprimir', tipo='ID')
        # elif ext == 'PDF':
            # self.alterna_janela(1, 1)
            # self.driver.switch_to.frame(self.driver.find_element_by_id('conteudoIframe'))
            # if not aguarda_presenca_elemento(self.driver, 'open-button', tipo='ID', tempo=45, latencia=0.2):
            #     raise MildException('erro download de PDF', self.uf, self.plataforma, self.prc_id)
            #
            # self.driver.find_element_by_id('open-button').click()
        elif ext == 'PNG' or ext == 'JPG' or ext == 'JPEG' or ext == 'GIF':
            self.alterna_janela((self.grau), 1, not_in_guid=self.handles)
            self.driver.switch_to.frame(self.driver.find_element_by_id('conteudoIframe'))
            if not aguarda_presenca_elemento(self.driver, '/html/body/img', tempo=45, latencia=0.2):
                raise MildException('erro download de imagem', self.uf, self.plataforma, self.prc_id)

            self.driver.execute_script('setTimeout(function() { window.print(); }, 0);')

        wh = self.driver.window_handles
        if len(wh) > self.grau:
            self.alterna_janela(self.grau, 1, not_in_guid=self.handles)
            try:
                err = self.driver.find_element_by_xpath('/html/body')
                if err:
                    if err.text.find('Erro acessar o documento') > -1:
                        return False
            except:
                pass

        return True

    def fecha_download(self, ext):

        all_guid = self.driver.window_handles
        for guid in all_guid:
            if guid not in self.handles:
                self.driver.switch_to.window(guid)
                self.driver.close()


        # if ext == 'PNG' or ext == 'JPG' or ext == 'JPEG':
        #     if len(self.driver.window_handles) > (self.grau):
        #         self.driver.close()
        #
        # while len(self.driver.window_handles) > (self.grau):
        #     time.sleep(0.5)
        #     try:
        #         self.driver.switch_to.window(self.driver.window_handles[(self.grau)])
        #         self.driver.close()
        #     except Exception as e:
        #         tb = traceback.format_exc()
        #         print(tb)
        #         pass

        self.driver.switch_to.window(self.handles[self.active_window])

    # AGUARDA ATÉ QUE A ANIMAÇÃO DE LOADING ESTEJA OCULTA
    def wait(self, tempo=30):
        # time.sleep(0.2)
        wait = WebDriverWait(self.driver, 1)
        try:
            wait.until(EC.visibility_of_element_located((By.ID, id)))
        except TimeoutException:
            pass
        except UnexpectedAlertPresentException:
            try:
                self.driver.switch_to.alert.accept()
            except NoAlertPresentException:
                pass

        wait = WebDriverWait(self.driver, tempo)
        try:
            wait.until(EC.invisibility_of_element((By.ID, 'divInfraAviso')))
        except TimeoutException:
            raise MildException("Loading Timeout", self.uf, self.plataforma, self.prc_id, False)

        wait = WebDriverWait(self.driver, tempo)
        try:
            wait.until(EC.invisibility_of_element((By.ID, 'spnInfraAviso')))
        except TimeoutException:
            raise MildException("Loading Timeout", self.uf, self.plataforma, self.prc_id, False)



        return True