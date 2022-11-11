from Controllers.Tribunais.Eproc._eproc import *
from Controllers.Tribunais.segundo_grau import *
from selenium.webdriver.support.ui import Select

# CLASSE DA VARREDURA DO EPROC DE SEGUNDO GRAU. HERDA OS METODOS DAS CLASSES PLATAFORMA e EPROC
class Eproc2g(SegundoGrau, Eproc):

    def __init__(self):
        super().__init__()
        self.pagina_inicial_2g = ""
        self.diferenciar_id_download_2g = True
        self.handles = []


    # CONFERE SE OS RECURSOS ESTÃO NA BASE CASO EXISTA MAIS DE UM
    def confere_recursos(self, base, proc):
        if self.numero_original:
            return True

        if proc['rec_id'] is not None:
            return True

        res = self.insert_recursos(base, proc)
        Processo.update(base, proc['prc_id'], self.plataforma, res, {}, grau=2)
        return False

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''
        self.handles = []
        for i in range(0, 2):
            self.handles.append(self.driver.current_window_handle)
            if not aguarda_presenca_elemento(self.driver, 'sbmEntrar', tipo='ID'):
                return False

            if usuario is None:
                self.driver.find_element_by_id('lnkEntrarCert').click()
            else:
                self.driver.find_element_by_id('txtUsuario').send_keys(usuario)
                self.driver.find_element_by_id('pwdSenha').send_keys(senha)
                self.driver.find_element_by_xpath('//*[@id="frmLogin"]/div/div[3]/button').click()

            try_click(self.driver, 'tr1', tipo='ID')

            if not self.reiniciar_navegador:
                if not aguarda_presenca_elemento(self.driver, 'btnProfile', tipo='ID', tempo=900):
                    return False
            else:
                if not aguarda_presenca_elemento(self.driver, 'btnProfile', tipo='ID'):
                    return False

            body = self.driver.find_element_by_tag_name('body').get_attribute('class')
            if body != 'instancia-'+str(i+1)+'g':
                print("Erro ao logar na "+str(i+1)+"a instancia")
                return False
                # raise CriticalException("Erro ao logar na "+str(i+1)+"a instancia", self.uf, self.plataforma, self.prc_id, False)

            if i == 0:
                self.driver.execute_script("window.open('" + self.pagina_inicial_2g + "', '_blank')")
                self.alterna_janela()

        self.alterna_janela(0, 2, aguarda_janela=False)
        return True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        self.active_window = 0
        # if not self.numero_original:
        #     self.alterna_janela(0, 2, aguarda_janela=False)
        #     # result = self.format_busca(numero_busca)
        #     result = super().busca_processo(numero_busca)
        #     if result:
        #         prc_classe = self.driver.find_element_by_id('txtClasse').text
        #         if find_string(prc_classe, ('Recurso', 'Apelação', 'Agravo')):
        #             return False
        #
        #     return result
        # else:
        if not self.buscar_origem and self.numero_original and str(self.numero_original) in ('1', '2'):
            return self.abre_processo(int(self.numero_original)-1, numero_busca)
        else:
            for i in range(0, 2):
                # CONFERE SE O PROCESSO FOI LOCALIZADO
                if self.abre_processo(i, numero_busca):
                    n1 = ajusta_numero(self.proc_data['prc_numero'])
                    # SE NÃO TIVER RECURSO CADASTRADO E O NUMERO SENDO BUSCADO É DIFERENTE DO PROCESSO PRINCIPAL, ELE INSERE UM NOVO RECURSO
                    if not (i == 0 and n1 == numero_busca):
                        if self.rec_id is None:
                            result = Recurso.select(self.conn_atual, self.prc_id, rec_numero=numero_busca, rec_plt_id=7)
                            if len(result) == 0:
                                Recurso.insert(self.conn_atual, {'rec_prc_id': self.prc_id, 'rec_numero': numero_busca, 'rec_codigo': i+1, 'rec_plt_id': self.plataforma})

                        if i == 0:
                            self.insert_recursos(self.conn_atual, self.proc_data)
                        return True

            # CASO O RECURSO TENHA SIDO INSERIDO ANTERIORMENTE, MAS PERTENCE AO 1º GRAU, APAGA o RECURSO E INSERE COMO PROCESSO
            if not self.buscar_origem and self.rec_id is not None and self.proc_data['rec_codigo'] is None:
                self.insere_novo_processo(numero_busca)
                # Recurso.update_simples(self.active_conn, self.rec_id, {'rec_status': 'Encerrado', 'rec_classe': 'Não se aplica'})
                Recurso.delete_rec(self.active_conn, self.rec_id)
                raise MildException("Processo não pertencente ao 2º grau", self.uf, self.plataforma, self.prc_id)

        return False

    # MÉTODO PARA ABRIR PROCESSO
    def abre_processo(self, indice, numero_busca):
        self.alterna_janela(indice, 2, aguarda_janela=False, guid=self.handles[indice])
        # result = self.format_busca(numero_busca)
        result = super().busca_processo(numero_busca)
        if result:
            self.active_window = indice
            prc_classe = self.driver.find_element_by_id('txtClasse')
            if prc_classe:
                if indice == 1:
                    return True

                if find_string(prc_classe.text, ('Recurso', 'Apelação', 'Agravo',)):
                    return True
                else:
                    colegiado = self.driver.find_element_by_id('txtOrgaoColegiadoTR')
                    if colegiado and colegiado.is_displayed():
                        return True

        return False

    # MÉTODO PARA FORMATAR A BUSCA DO PROCESSO
    def format_busca(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''

        els = self.driver.find_elements_by_xpath('//*[@id="main-menu"]/li/ul/li/a')
        for el in els:
            url = el.get_attribute('href')
            if url.find('processo_consultar') > -1:
                self.driver.get(url)
                break

        inicio = time.time()
        while True:
            if time.time() - inicio > 30:
                raise CriticalException("Erro ao limpar Campo de busca", self.uf, self.plataforma, self.prc_id, False)
            self.wait()
            self.process_main_child = foca_janela(self.process_main_child)

            campo_busca = self.driver.find_element_by_id('numNrProcesso')
            if not campo_busca:
                raise CriticalException("Campo de busca não localizado", self.uf, self.plataforma, self.prc_id, False)

            try:
                campo_busca.clear()
                break
            except:
                self.driver.refresh()
                time.sleep(3)

        self.driver.find_element_by_xpath('//*[@id="divChkExibirBaixados"]/dl/dd/input').click()

        try:
            campo_busca.send_keys(numero_busca)
            campo_busca.send_keys(Keys.ENTER)
        except StaleElementReferenceException:
            raise MildException("Página atualizada", self.uf, self.plataforma, self.prc_id, False)

        aguarda_alerta(self.driver, tempo=0.2)

        self.wait()

        if self.driver.find_element_by_id('txtCaptcha'):
            if self.driver.find_element_by_id('txtCaptcha').is_displayed():
                raise CriticalException("Captcha Detectado", self.uf, self.plataforma, self.prc_id, False)

        div_erro = self.driver.find_element_by_id('divInfraExcecao')
        if div_erro:
            if div_erro.text.upper().find('NÃO ENCONTRADO') > -1:
                return False

        return True

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
                    wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="tblPartesERepresentantes"]/tbody/tr['+str(len(trs)+1)+']')))
                except TimeoutException:
                    raise MildException('erro ao carregar outras partes', self.uf, self.plataforma, self.prc_id)
                    pass

        tipo_parte = self.driver.find_element_by_xpath('//*[@id="tblPartesERepresentantes"]/tbody/tr[1]/th[1]').text
        polo_td1 = ''
        polo_td2 = ''
        # if tipo_parte == 'AUTOR' or tipo_parte == 'REQUERENTE' or tipo_parte == 'EXEQUENTE' or tipo_parte == 'RECORRENTE' or tipo_parte == 'APELANTE':
        if find_string(tipo_parte, ('AUTOR','REQUERENTE','EXEQUENTE','RECORRENTE','APELANTE','AGRAVANTE')):
            polo_td1 = 'ativo'
            polo_td2 = 'passivo'


        i = 0
        trs = self.driver.find_elements_by_xpath('//*[@id="tblPartesERepresentantes"]/tbody/tr')
        if len(trs) == 1:
            raise MildException('erro ao carregar tabela de partes', self.uf, self.plataforma, self.prc_id)

        tipos = {'ativo': 'X', 'passivo': 'Y', 'terceiro': 'Z'}
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
                    if find_string(txt_td, ('(AUTOR)','REQUERENTE','EXEQUENTE','RECORRENTE','APELANTE','AGRAVANTE')):
                        polo_td = 'ativo'
                    elif find_string(txt_td, ('(RÉU)', 'REQUERIDO','EXECUTADO','RECORRIDO','APELADO','AGRAVADO')):
                        polo_td = 'passivo'
                    else:
                        if polo_td1 != '' and polo_td2 != '':
                            polo_td = polo_td1 if j == 1 else polo_td2
                        else:
                            continue

                    tipos[polo_td] = txt_td
                    prt_cpf_cnpj = 'Não Informado'
                    id_cpf = 'spnCpfParteAutor' if j == 1 else 'spnCpfParteReu'
                    cpf = td.find_elements_by_id(id_cpf+str(i))
                    if len(cpf) > 0:
                        prt_cpf_cnpj = cpf[0].text
                    partes[polo_td].append({'prt_nome': prt_nome, 'prt_cpf_cnpj': prt_cpf_cnpj})

                j += 1

            i += 1

        if tipos['ativo'] == tipos['passivo']:
            return {'ativo': [{'prt_nome': 'AMBOS',}, ],}
        return partes

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []

        tipo_parte = self.driver.find_element_by_xpath('//*[@id="tblPartesERepresentantes"]/tbody/tr[1]/th[1]').text
        polo_td1 = ''
        polo_td2 = ''
        if tipo_parte == 'AUTOR' or tipo_parte == 'REQUERENTE' or tipo_parte == 'EXEQUENTE' or tipo_parte == 'RECORRENTE' or tipo_parte == 'APELANTE':
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
                if find_string(txt_td, ('(AUTOR)', 'REQUERENTE', 'EXEQUENTE','RECORRENTE','APELANTE')):
                    polo = 'ativo'
                elif find_string(txt_td, ('(RÉU)', 'REQUERIDO', 'EXECUTADO','RECORRIDO','APELADO')):
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

                    resps.append({'prr_nome': nome, 'prr_oab': oab, 'prr_cargo': 'Advogado', 'prr_parte': polo})

        return resps

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        rec = {}
        if self.active_window == 0:
            prc_classe = self.driver.find_element_by_id('txtClasse')
            if not find_string(prc_classe.text, ('Recurso', 'Apelação', 'Agravo',)):
                colegiado = self.driver.find_element_by_id('txtOrgaoColegiadoTR')
                if not colegiado or not colegiado.is_displayed():
                    raise MildException("Não é um recurso", self.uf, self.plataforma, self.prc_id)

        rec['rec_status'] = get_status(self.movs, status_atual, grau=2)
        # print(self.active_window)
        body_class = self.driver.find_element_by_tag_name('body').get_attribute('class')
        rec['rec_codigo'] = 2 if body_class.find('instancia-2g') > -1 else 1
        if self.proc_data['rec_codigo'] is not None and str(rec['rec_codigo']) != str(self.proc_data['rec_codigo']):
            print(type(rec['rec_codigo']),type(self.proc_data['rec_codigo']))
            print(rec['rec_codigo'], self.proc_data['rec_codigo'])
            raise MildException("Janela diferente da original", self.uf, self.plataforma, self.prc_id)
        # rec['rec_codigo'] = self.active_window+1

        # prc_classe = self.driver.find_element_by_id('txtClasse').text

        serventia = self.driver.find_element_by_id('txtOrgaoJulgadorJEF')
        if serventia:
            rec['rec_orgao'] = serventia.text
        else:
            rec['rec_orgao'] = self.driver.find_element_by_id('txtOrgaoJulgador').text

        rec['rec_classe'] = self.driver.find_element_by_id('txtClasse').text
        rec['rec_relator'] = self.driver.find_element_by_id('txtMagistrado').text
        rec['rec_numero'] = self.driver.find_element_by_id('txtNumProcesso').text
        rec_distribuicao = self.driver.find_element_by_id('txtAutuacao').text
        rec['rec_distribuicao'] = datetime.strptime(rec_distribuicao, '%d/%m/%Y %H:%M:%S')

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
        campos = {'Valor da Causa': 'rec_valor', 'Nível de Sigilo': 'rec_segredo',}
        for tr in trs:
            i = 0
            tds = tr.find_elements_by_xpath('td')
            for td in tds:
                i += 1
                txt = td.text
                for c in campos:
                    if txt.find(c) > -1:
                        rec[campos[c]] = tds[i].text
                        break

        if 'rec_segredo' in rec:
            rec['rec_segredo'] = False if rec['rec_segredo'].find('Sem Sigilo') > -1 else True

        # EXIBE TABELA DE ASSUNTOS
        self.driver.execute_script("infraAbrirFecharElementoHTML('conteudoAssuntos2', 'imgStatusAssunto');")
        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="conteudoAssuntos2"]/table/tbody/tr[2]')))
        except TimeoutException:
            pass

        trs = self.driver.find_elements_by_xpath('//*[@id="conteudoAssuntos2"]/table/tbody/tr/td[2]')
        rec_assunto = []
        for tr in trs:
            rec_assunto.append(tr.text)

        rec['rec_assunto'] = " | ".join(rec_assunto)

        return rec