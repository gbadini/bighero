from Config.helpers import *
from Controllers.Tribunais.primeiro_grau import *
from selenium.webdriver.common.keys import *
from Models.processoModel import *
import sys, time, shutil
import urllib.parse as urlparse
from urllib.parse import parse_qs

# CLASSE DA VARREDURA DO ESAJ. HERDA OS METODOS DA CLASSE PLATAFORMA
class Esaj(PrimeiroGrau):

    def __init__(self):
        super().__init__()
        self.plataforma = 5
        self.id_mensagem_erro = 'mensagemRetorno'
        self.versao = None
        self.download_click = False
        self.tabela_partes = 'tablePartesPrincipais'
        self.url_base = ""
        self.movs = []

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''
        if not aguarda_presenca_elemento(self.driver, 'usernameForm', tipo='ID'):
            return False

        if usuario is None:
            self.driver.find_element_by_id('linkAbaCertificado').click()
        else:
            self.driver.find_element_by_id('usernameForm').send_keys(usuario)
            self.driver.find_element_by_id('passwordForm').send_keys(senha)
            self.driver.find_element_by_id('pbEntrar').click()

        try_click(self.driver, 'confirmarDados', tipo='ID')

        # erro = self.driver.find_element_by_xpath('//*[@id="spwTabelaMensagem"]/table[1]/tbody/tr[2]/td[2]/li')
        # if erro and erro.text.find('Não foi possível executar esta operação') > -1:
        #     self.driver.find_element_by_id('pbVoltar').click()

        if not aguarda_presenca_elemento(self.driver, '//*[@id="identificacao"]/strong'):
            return False

        if check_text(self.driver, '/html/body/table[2]/tbody/tr/td[2]/table/tbody/tr[2]/td/button', 'Acessar nova versão do e-SAJ'):
            self.driver.find_element_by_xpath('/html/body/table[2]/tbody/tr/td[2]/table/tbody/tr[2]/td/button').click()


        return True

    # CONFERE SE O CÓDIGO É VALIDO
    def check_codigo(self, codigo):
        '''
        :param str codigo: codigo _GET de acesso
        '''
        if codigo is None:
            return False

        if codigo.strip() == '' or codigo.find('&') == -1:
            return False

        return True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        # self.driver.get(self.pagina_busca)
        inicio_cnj = numero_busca[:13]
        fim_cnj = numero_busca[16:]
        try_click(self.driver, 'conpassButtonClose', tipo='ID')

        inicio_tj = 'XXX'
        fim_tj = 'XXX'

        if not aguarda_presenca_elemento(self.driver,'numeroDigitoAnoUnificado', tipo='ID'):
            raise CriticalException("Campo de busca não localizado", self.uf, self.plataforma, self.prc_id, False)

        inicio = time.time()
        while inicio_cnj != inicio_tj or fim_cnj != fim_tj:
            if time.time() - inicio > 15:
                    raise MildException("Erro ao imputar CNJ no campo", self.uf, self.plataforma, self.prc_id)

            try:
                self.driver.find_element_by_id('numeroDigitoAnoUnificado').clear()
            except ElementNotVisibleException:
                self.driver.refresh()
                self.driver.find_element_by_id('numeroDigitoAnoUnificado').clear()
            except:
                raise MildException("Campo de Busca não localizado", self.uf, self.plataforma, self.prc_id, False)

            for c in inicio_cnj:
                self.driver.find_element_by_id('numeroDigitoAnoUnificado').send_keys(c)

            inicio_tj = self.driver.find_element_by_id('numeroDigitoAnoUnificado').get_attribute('value')
            inicio_tj = inicio_tj.replace('.','').replace('-','').replace(' ','')

            self.driver.find_element_by_id('foroNumeroUnificado').clear()
            for c in fim_cnj:
                self.driver.find_element_by_id('foroNumeroUnificado').send_keys(c)

            fim_tj = self.driver.find_element_by_id('foroNumeroUnificado').get_attribute('value')
            fim_tj = fim_tj.replace('.','').replace('-','').replace(' ','')


        self.driver.find_element_by_id('numeroDigitoAnoUnificado').send_keys(Keys.ENTER)

        try_click(self.driver, '//*[@id="conpass-tag"]/div/div[2]/div[1]')

        msg_erro = self.driver.find_element_by_id(self.id_mensagem_erro)
        if msg_erro:
            txt = msg_erro.text
            if find_string(txt, ('deve ser preenchido', 'inválido', 'tente novamente mais tarde',)):
                raise MildException("Erro na Busca", self.uf, self.plataforma, self.prc_id)

            if find_string(txt, ('Não existem informações disponíveis',)):
                return False

        return True

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        if self.driver.find_element_by_class_name("g-recaptcha"):
            if self.driver.find_element_by_class_name("g-recaptcha").is_displayed():
                raise CriticalException("Captcha Detectado", self.uf, self.plataforma, self.prc_id)

        xpaths = (
            '//*[@id="containerDadosPrincipaisProcesso"]/div[1]/div/div/span',
            '/html/body/div[1]/div[2]/div/div[1]/div/span[1]',
            '/html/body/div[1]/div[2]/div/div[1]/div/div/span[1]',
            '/html/body/table[4]/tbody/tr/td/table[2]/tbody/tr[1]/td[2]/table/tbody/tr/td/span[1]',
            '/html/body/div/table[4]/tbody/tr/td/div[1]/table[2]/tbody/tr[1]/td[2]/table/tbody/tr/td/span[1]',
            '//*[@id="blocoDados"]/ul/li[1]/span'
        )
        numero_site = 'edfwefewfewf'
        for xp in xpaths:
            # print(xp)
            el = self.driver.find_element_by_xpath(xp)
            if el:
                cnj = localiza_cnj(el.text)
                if cnj:
                    numero_site = ajusta_numero(cnj)
                    if numero_busca == numero_site:
                        return True

        raise MildException("Número CNJ Diferente "+numero_busca+" | "+numero_site, self.uf, self.plataforma, self.prc_id)

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):

        # VERIFICA SE EXISTE LISTAGEM DE PROCESSOS NO RESULTADO E CLICA NO CORRESPONDENTE
        if self.driver.find_element_by_id('listagemDeProcessos'):
            listagem = localiza_elementos(self.driver,('//*[@id="listagemDeProcessos"]/ul/li/div/div/div[1]/a','//*[@id="listagemDeProcessos"]/ul[1]/li/div/div/div[1]/a', '//*[@id="listagemDeProcessos"]/div[2]/div/div[1]/a'), retorna_multiplos=True)
            if listagem:
                for lp in listagem:
                    numero_site = ajusta_numero(lp.text)
                    href = lp.get_attribute('href')

                    if numero_busca == numero_site and (codigo is None or href.find(codigo) > -1):
                        lp.click()
                        break

        # VERIFICA SE EXISTE LISTAGEM DE PROCESSOS NO POPUP E CLICA NO CORRESPONDENTE
        listagem = self.driver.find_elements_by_xpath('//*[@id="modalIncidentes"]/div/div/div/article/section/div[1]/div[1]')
        for lp in listagem:
            numero_site = lp.find_element_by_xpath('div/em[1]').text
            numero_site = ajusta_numero(numero_site)
            if numero_busca == numero_site:
                lp.find_element_by_xpath('input[1]').click()
                # time.sleep(2)
                # self.driver.find_element_by_xpath('//*[@id="modalIncidentes"]/div/div[2]/div/article/section/div[1]/div[1]/input').click()
                self.driver.find_element_by_id('botaoEnviarIncidente').click()
                break


        # CONFERE SE EXISTE POPUP DE SENHA
        try:
            self.driver.find_element_by_id('botaoFecharPopupSenha').click()
            return True
        except:
            pass

        self.confere_cnj(numero_busca)
        return False

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        xpaths = ('//*[@id="tabelaUltimasMovimentacoes"]/tr[1]/td[3]/span','//*[@id="tabelaUltimasMovimentacoes"]/tr[1]/td[3]','//*[@id="tabelaUltimasMovimentacoes"]/tbody/tr[1]/td[3]/span','//*[@id="tabelaUltimasMovimentacoes"]/tbody/tr[1]/td[3]','/html/body/div[2]/table[5]/tbody/tr/td')
        esp = localiza_elementos(self.driver, xpaths, desconsidera_vazio=True, desconsidera_oculto=True)
        if not esp:
            div = self.driver.find_element_by_class_name('div-conteudo')
            if div:
                if div.text.upper().find('NÃO HÁ MOVIMENTAÇÕES PARA ESTE PROCESSO') > -1:
                    return True

            raise MildException("Última Mov não localizada", self.uf, self.plataforma, self.prc_id)

        acp_esp = esp.text
        if acp_esp.upper().find('NÃO HÁ MOVIMENTAÇÕES') > -1:
            return True

        movs = self.captura_movimentos(False, base, self.rec_id)
        return len(movs) == 0


        xpaths = ('//*[@id="tabelaUltimasMovimentacoes"]/tr[1]/td[1]', '//*[@id="tabelaUltimasMovimentacoes"]/tbody/tr[1]/td[1]')
        acp_cad = localiza_elementos(self.driver, xpaths, desconsidera_vazio=True)
        if not acp_cad:
            raise MildException("Data Cadastro não localizado", self.uf, self.plataforma, self.prc_id)

        data_cad = datetime.strptime(acp_cad.text, '%d/%m/%Y')

        return Acompanhamento.compara_mov(base, prc_id, acp_esp, data_cad, self.plataforma, self.grau, rec_id=self.rec_id)

    # CAPTURA ACOMPANHAMENTOS DO PROCESSO
    def acompanhamentos(self, proc_data, completo, base):
        '''
        :param datetime Última movimentação registrada na base
        :param bool Realiza a captura completa das movimentações
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        try:
            self.driver.execute_script("document.getElementsByTagName('footer')[0].style.display = 'none';")
            self.driver.execute_script("document.getElementsByClassName('conpassAssistant')[0].style.display = 'none';")
        except:
            pass
        try:
            self.driver.execute_script("$('#maisDetalhes').addClass('show')")
        except:
            raise MildException('erro ao executar JS', self.uf, self.plataforma, self.prc_id)

        self.driver.execute_script("window.scrollTo(0,0);")

        try_click(self.driver, '//*[@id="conpass-tag"]/div/div[2]/div[1]')


        # if completo:
        try_click(self.driver, 'linkmovimentacoes', tipo='ID')


        rec_id = proc_data['rec_id'] if 'rec_id' in proc_data else None
        return self.captura_movimentos(completo, base, rec_id)

    def captura_movimentos(self, completo, base, rec_id=None):
        # ultima_mov = proc_data['cadastro']
        prc_id = self.prc_id
        # proc_data['prc_id']
        self.movs = []
        movs = []
        xpaths = ('//*[@id="tabelaTodasMovimentacoes"]/tr', '//*[@id="tabelaUltimasMovimentacoes"]/tr', '//*[@id="tabelaTodasMovimentacoes"]/tbody/tr', '//*[@id="tabelaUltimasMovimentacoes"]/tbody/tr', '/html/body/div[2]/table[5]/tbody/tr/td', '/html/body/div[2]/table[6]/tbody/tr/td')
        movimentos = localiza_elementos(self.driver, xpaths, desconsidera_vazio=True, desconsidera_oculto=True, retorna_multiplos=True)
        if not movimentos:
            div = self.driver.find_element_by_class_name('div-conteudo')
            if div:
                if div.text.upper().find('NÃO HÁ MOVIMENTAÇÕES PARA ESTE PROCESSO') > -1:
                    return []

            raise MildException("Movs não localizadas", self.uf, self.plataforma, self.prc_id)

        acp_esp = movimentos[0].text
        if acp_esp.upper().find('NÃO HÁ MOVIMENTAÇÕES') > -1:
            return []

        if len(movimentos) < 2:
            div = self.driver.find_element_by_class_name('div-conteudo')
            if div:
                if div.text.find('NÃO HÁ MOVIMENTAÇÕES PARA ESTE PROCESSO') > -1:
                    return []


        # BUSCA MOVIMENTAÇÕES DO PROCESSO NA BASE
        lista = Acompanhamento.lista_movs(base, prc_id, self.plataforma, rec_id=rec_id, acp_grau=self.grau)
        # print(lista)
        capturar = True
        fim = False
        i = 0
        for mov in movimentos:
            i += 1
            acp_cadastro = mov.find_element_by_xpath('td[1]').text
            acp_cadastro = acp_cadastro.replace('&nbsp;','').replace("\r", '').replace("\n",'')
            r = re.search('(\\d+)(\\/)(\\d+)(\\/)(\\d+)', acp_cadastro)
            if not r:
                continue

            acp_cadastro = datetime.strptime(r.group(0)+' 00:00:00', '%d/%m/%Y %H:%M:%S')

            txt = mov.find_element_by_xpath('td[3]').get_attribute('innerHTML')
            txt = txt.replace('&nbsp;', '').replace('\r', '').replace('\n', '').replace('"', '').replace("'", '')
            txts = txt.split('<br>')
            acp_tipo = txts[0]
            acp_tipo = strip_html_tags(acp_tipo)
            el = localiza_elementos(mov, ('td[3]/span',), desconsidera_vazio=True)
            acp_esp = strip_html_tags(el.text) if el else acp_tipo

            # if completo:
            capturar = True

            esp_site = corta_string(acp_esp)
            for l in lista:
                esp_base = corta_string(l['acp_esp'])

                if acp_cadastro == l['acp_cadastro'] and esp_site == esp_base:
                    capturar = False
                    break

            # if not capturar and not completo and i >= 10:
            #     break

            acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp, 'acp_tipo': acp_tipo}
            if capturar:
                movs.append(acp)

            self.movs.append({**acp, 'novo': capturar})

        if len(self.movs) == 0:
            raise MildException("Erro ao capturar Movs", self.uf, self.plataforma, self.prc_id)

        return movs

    # CAPTURA AUDIENCIAS DO PROCESSO
    def audiencias(self):
        adcs = []

        for mov in self.movs:
            # if not self.completo and not mov['novo']:
            #     break

            esp = mov['acp_esp'].upper().strip()
            esp = esp.replace('Ê','E')
            tipo = mov['acp_tipo'].upper().strip()
            tipo = tipo.replace('Ê','E')

            fs = find_string(esp, ('DESIGNO AUDIENCIA DE INSTRUÇÃO','TEOR DO ATO: CONCILIAÇÃO DATA:','DESIGNEI A AUDIÊNCIA DE INSTRUÇÃO E JULGAMENTO','PARA A AUDIENCIA DE CONCILIAÇÃO DESIGNADA PARA O DIA','DESIGNEI O DIA','PARA A REALIZAÇÃO DA AUDIENCIA','DÁ A PARTE POR INTIMADA PARA COMPARECIMENTO À AUDI','DÁ A PARTE POR INTIMADA PARA, AUDIENCIA DE','INTIMADO DA AUDIENCIA DE','INTIMADA PARA COMPARECER À AUDIENCIA'))
            if (not fs) and tipo not in ('DE CONCILIAÇÃO','DE INSTRUÇÃO E JULGAMENTO','INFRUTÍFERA'):
                f = tipo.find('AUDIENCIA')
                if f == -1 or f > 10 or len(esp) < 35 or esp == 'AUDIENCIA' or esp == 'AUDIENCIA DESIGNADA':
                    continue
                if esp.find('AUDIENCIA DESIGNADA') > 0 or esp.find('AUDIENCIA REDESIGNADA') > 0 or tipo.find('AUDIENCIA DESIGNADA') > 0 or tipo.find('AUDIENCIA REDESIGNADA') > 0 or esp.find('FICA A PRESENTE REDESIGNADA') > 0:
                    continue

            # fs = find_string(esp, ('DESIGNEI A AUDIÊNCIA DE INSTRUÇÃO E JULGAMENTO','PARA A AUDIENCIA DE CONCILIAÇÃO DESIGNADA PARA O DIA','DESIGNEI O DIA','PARA A REALIZAÇÃO DA AUDIENCIA','DÁ A PARTE POR INTIMADA PARA COMPARECIMENTO À AUDI','INTIMADO DA AUDIENCIA DE','INTIMADA PARA COMPARECER À AUDIENCIA'))
            # print('esp',esp)
            dia = localiza_data(esp, True)
            if not dia:
                continue

            # print('dia', dia)
            aud = localiza_audiencia(dia + ' - ' + esp, formato_data='%Y-%m-%d %H:%M',
                                     formato_re='(\\d+)(\\-)(\\d+)(\\-)(\\d+)(\\s+)(\\d+)(\\:)(\\d+)')
            # print('aud', aud)

            # if fs:
            #     dia = localiza_data(esp, True)
            #     print('dia',dia)
            #     aud = localiza_audiencia(dia + ' - ' + esp, formato_data='%Y-%m-%d %H:%M', formato_re='(\\d+)(\\-)(\\d+)(\\-)(\\d+)(\\s+)(\\d+)(\\:)(\\d+)')
            #     print('aud',aud)
            # elif esp.find('DÁ A PARTE POR INTIMADA PARA, AUDIENCIA DE') == 0:
            #     aud = localiza_audiencia(esp.replace(',',''), formato_re='(\\d+)(\\/)(\\d+)(\\/)(\\d+)(\\s+)(\\d+)(\\:)(\\d+)')
            # else:
            #     aud = localiza_audiencia(esp, formato_re='(\\d+)(\\/)(\\d+)(\\/)(\\d+)(\\s+)(HORA)(\\s+)(\\d+)(\\:)(\\d+)')
            #     if not aud:
            #         aud = localiza_audiencia(esp, formato_re='(\\d+)(\\/)(\\d+)(\\/)(\\d+)(\\,)(\\s+)(AS)(\\s+)(\\d+)(H)(\\d+)',formato_data='%d/%m/%Y, AS %Hh%M')

            if not aud:
                continue

            achei = False
            for adc in adcs[:]:
                if adc['prp_data'] == aud['prp_data']:
                    if 'prp_status' in aud and aud['prp_status'] != 'Designada':
                        adcs.remove(adc)
                    else:
                        achei = True

                    break

            if achei:
                continue

            if 'prp_status' not in aud:
                aud['prp_status'] = 'Designada'

            if 'prp_tipo' not in aud:
                aud['prp_tipo'] = 'Audiência'
                # raise MildException("Audiência - Tipo não localizado: "+esp, self.uf, self.plataforma, self.prc_id)

            serventia = None
            p = esp.find('LOCAL')
            if p > -1:
                serventia = mov['acp_esp'][p+5:].strip()
                p = serventia.find('Situacão')
                if p > -1:
                    serventia = serventia[:p].strip()

                serventia = serventia.strip(':').strip()

            aud['prp_serventia'] = serventia
            aud['data_mov'] = mov['acp_cadastro']
            adcs.append(aud)

        tab_auds = self.driver.find_elements_by_xpath('/html/body/div/table/tbody')
        for ta in tab_auds:
            th = ta.find_elements_by_xpath('tr[1]/th[2]')
            if len(th) == 0:
                continue

            if len(th) > 0:
                if th[0].text.find('Audiência') == -1:
                    continue

            trs = ta.find_elements_by_xpath('tr')
            del trs[0]
            for tr in trs:
                if len(tr.find_elements_by_xpath('td[3]')) == 0:
                    continue

                aud = localiza_audiencia(tr.text, formato_data='%d/%m/%Y', formato_re='(\\d+)(\\/)(\\d+)(\\/)(\\d+)')
                if not aud:
                    continue

                achei = False
                for adc in adcs:
                    if adc['prp_data'].date() == aud['prp_data'].date():
                        achei = True
                        break

                if achei:
                    continue

                aud['data_mov'] = datetime.now()
                aud['prp_serventia'] = None
                adcs.append(aud)

        return adcs

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo': [], 'passivo': [], 'terceiro':[]}

        # IDENTIFICA A VERSÃO DO E-SAJ
        if self.versao is None:
            self.versao = 1 if self.driver.find_element_by_class_name('unj-entity-header') else 2

        # if self.versao == 1:
        #     trs = self.driver.find_elements_by_class_name('nomeParteEAdvogado')
        # else:
        #     trs = localiza_elementos(self.driver, ('//*[@id="tablePartesPrincipais"]/tbody/tr/td[2]', '//*[@id="tablePartesPrincipais"]/tbody/tr/td[2]'), retorna_multiplos=True)
        self.tabela_partes = 'tablePartesPrincipais'
        if try_click(self.driver, 'linkpartes', 'ID'):
            wait = WebDriverWait(self.driver, 10)
            try:
                wait.until(EC.visibility_of_element_located((By.ID, 'tableTodasPartes')))
            except:
                try_click(self.driver, 'linkpartes', 'ID')
                wait = WebDriverWait(self.driver, 10)
                try:
                    wait.until(EC.visibility_of_element_located((By.ID, 'tableTodasPartes')))
                except:
                    raise MildException('erro ao carregar tabela de partes', self.uf, self.plataforma, self.prc_id)
            self.tabela_partes = 'tableTodasPartes'

        trs = self.driver.find_elements_by_xpath('//*[@id="'+self.tabela_partes+'"]/tbody/tr')

        if len(trs) == 0:
            raise MildException('tr partes vazio', self.uf, self.plataforma, self.prc_id)

        nomes = []
        for tr in trs:
            polo = ''
            td1 = tr.find_element_by_xpath('td[1]').text
            if find_string(td1,self.titulo_partes['ignorar']):
                continue

            if find_string(td1,self.titulo_partes['ativo']):
                polo = 'ativo'
            if find_string(td1,self.titulo_partes['passivo']):
                polo = 'passivo'
            if find_string(td1,self.titulo_partes['terceiro']):
                polo = 'terceiro'

            if polo == '':
                raise MildException("polo vazio "+td1, self.uf, self.plataforma, self.prc_id)

            td2 = tr.find_element_by_xpath('td[2]')
            html = td2.get_attribute('innerHTML')

            prts = html.split('<br>')

            for prt in prts:
                prt_nome = strip_html_tags(prt)

                if not find_string(prt_nome,('ADVOGADO:','ADVOGADA:')):
                    if prt_nome in nomes:
                        continue
                    nomes.append(prt_nome)
                    partes[polo].append({'prt_nome': prt_nome, 'prt_cpf_cnpj': 'Não Informado'})

        return partes

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        prc = {}
        # self.driver.execute_script("$('#botaoExpandirDadosSecundarios').click()")
        # self.driver.execute_script("$('#maisDetalhes').addClass('show')")
        self.driver.execute_script("window.scrollTo(0,0);")

        # LOCALIZA STATUS DO PROCESSO
        prc['prc_status'] = get_status(self.movs, status_atual)

        # LOCALIZA NRO CNJ
        if self.versao == 1:
            numero2 = self.driver.find_element_by_id('numeroProcesso')
            if numero2:
                prc['prc_numero2'] = numero2.text
            else:
                xpaths = (
                    '//*[@id="containerDadosPrincipaisProcesso"]/div[1]/div/div/span',
                    '/html/body/div[1]/div[2]/div/div[1]/div/span[1]',
                    '/html/body/div[1]/div[2]/div/div[1]/div/div/span[1]',
                    '/html/body/table[4]/tbody/tr/td/table[2]/tbody/tr[1]/td[2]/table/tbody/tr/td/span[1]',
                    '/html/body/div/table[4]/tbody/tr/td/div[1]/table[2]/tbody/tr[1]/td[2]/table/tbody/tr/td/span[1]'
                )

                for xp in xpaths:
                    el = self.driver.find_element_by_xpath(xp)
                    if el:
                        cnj = localiza_cnj(el.text)
                        if cnj:
                            prc['prc_numero2'] = cnj
                            break

        if self.versao == 1:
            # divs = self.driver.find_elements_by_xpath('/html/body/div[1]/div/div/div/div')
            main_div = self.driver.find_element_by_xpath('/html/body/div[1]')
            divs = main_div.find_elements_by_xpath("//div[contains(@class, 'row')]/div")
        else:
            divs = self.driver.find_elements_by_xpath('/html/body/table[4]/tbody/tr/td/table[2]/tbody/tr')

        campos = {'Valor da ação': 'prc_valor_causa', 'Assunto': 'prc_assunto', 'Classe': 'prc_classe', 'Vara': 'prc_serventia', 'Foro': 'prc_comarca2', 'Distribuição': 'prc_distribuicao', 'Processo': 'prc_numero2' }

        i = 1
        for div in divs:
            i += 1
            try:
                if self.versao == 1:
                    label = div.find_element_by_tag_name('span').text
                else:
                    label = div.find_element_by_xpath('td[1]').text
            except:
                continue

            if label.strip() == '' and 'prc_serventia' not in prc and i > 4:
                prc['prc_serventia'] = div.find_element_by_xpath('td[2]').text
                prc['prc_comarca2'] = prc['prc_serventia']
                continue

            for c in campos:
                if label.upper().find(c.upper()) > -1:
                    if self.versao == 1:
                        txt = div.find_element_by_tag_name('div').text
                    else:
                        txt = div.find_element_by_xpath('td[2]').text

                    if campos[c] in prc:
                        prc[campos[c]] += ' '+txt
                    else:
                        prc[campos[c]] = txt
                    break

        if 'prc_distribuicao' in prc:
            r = re.search('(\\d+)(\\/)(\\d+)(\\/)(\\d+)(\\s+)(às)(\\s+)(\\d+)(:)(\\d+)', prc['prc_distribuicao'])
            prc_distribuicao = r.group(0).replace(' às', '')
            prc['prc_distribuicao'] = datetime.strptime(prc_distribuicao, '%d/%m/%Y %H:%M')

        prc['prc_comarca2'] = localiza_comarca(prc['prc_comarca2'], self.uf)
        prc['prc_numero2'] = localiza_cnj(prc['prc_numero2'])

        url = self.driver.execute_script('return window.location')
        parsed = urlparse.urlparse(url['href'])
        parse_qs(parsed.query)
        url_params = parse_qs(parsed.query)
        if 'processo_codigo' in url_params:
            prc['prc_codigo'] = url_params['processo_codigo'][0]+'&processo.foro='+url_params['processo_foro'][0]
        elif 'processo.codigo' in url_params:
            prc['prc_codigo'] = url_params['processo.codigo'][0]+'&processo.foro='+url_params['processo.foro'][0]
        else:
            htmls = self.driver.find_elements_by_tag_name('script')
            for html in htmls:
                inner = html.get_attribute('innerHTML')
                p = inner.find('cdProcesso')
                if p > -1:
                    codigo = inner[p+11:]
                    p = codigo.find('&')
                    codigo = codigo[:p]

                    p = inner.find('cdForo=')
                    foro = inner[p+7:]
                    p = foro.find('&')
                    foro = foro[:p]
                    prc['prc_codigo'] = codigo+'&processo.foro='+foro
                    break

        return prc

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []

        juiz = ''
        # CAPTURA NOME JUIZ
        if self.versao == 1:
            main_div = self.driver.find_element_by_xpath('/html/body/div[1]')
            divs = main_div.find_elements_by_xpath("//div[contains(@class, 'row')]/div")
        else:
            divs = self.driver.find_elements_by_xpath('/html/body/div/table[4]/tbody/tr/td/div[1]/table[2]/tbody/tr/td[2]')

        for div in divs:
            try:
                if self.versao == 1:
                    titulo = div.find_element_by_tag_name('label').text
                else:
                    titulo = div.find_element_by_tag_name('td[1]').text
            except:
                continue

            if titulo.find('Juiz') > -1:
                if self.versao == 1:
                    juiz = div.find_element_by_tag_name('div').text
                else:
                    juiz = div.find_element_by_tag_name('td[2]').text

        if juiz != '':
            resps.append({'prr_nome': juiz.strip(), 'prr_oab': '', 'prr_cargo': 'Juiz', 'prr_parte': ''})

        # CAPTURA NOME ADVOGADOS
        trs = self.driver.find_elements_by_xpath('//*[@id="'+self.tabela_partes+'"]/tbody/tr')
        nomes = []
        for tr in trs:
            polo = ''
            td1 = tr.find_element_by_xpath('td[1]').text
            if find_string(td1,self.titulo_partes['ignorar']):
                continue

            if find_string(td1,self.titulo_partes['terceiro']):
                continue

            if find_string(td1,self.titulo_partes['ativo']):
                polo = 'Polo Ativo'
            if find_string(td1,self.titulo_partes['passivo']):
                polo = 'Polo Passivo'

            td2 = tr.find_element_by_xpath('td[2]')

            html = td2.get_attribute('innerHTML')
            prts = html.split('<br>')
            for prt in prts:
               prr_nome = strip_html_tags(prt)
               if find_string(prr_nome,('ADVOGADO:','ADVOGADA:')):
                   if prr_nome in nomes:
                       continue
                   nomes.append(prr_nome)
                   prr_nome = prr_nome[15:] if prr_nome.find('Soc. Advogado') > -1 else prr_nome[10:]
                   resps.append({'prr_nome': prr_nome, 'prr_oab': None, 'prr_cargo': 'Advogado', 'prr_parte': polo})

        return resps

    # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS
    def download(self, prc_id, arquivos_base, pendentes, pasta_intermediaria):
        if self.grau == 2:
            return []

        arquivos = []
        total_arquivos = 0
        multipla_janela = False
        if self.download_click == False:
            if not self.driver.find_element_by_id('linkPasta'):
                btn2g = self.driver.find_element_by_partial_link_text('Consultar em 2ª instância')
                if not btn2g:
                    return []
                btn2g.click()
                self.alterna_janela()
                multipla_janela = True
                if not self.driver.find_element_by_id('pbVisualizarAutos'):
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    return []
                # href = self.driver.find_element_by_id('pbVisualizarAutos').get_attribute('href')
            else:
                href = self.driver.find_element_by_id('linkPasta').get_attribute('href')
        else:
            url = self.driver.execute_script('return window.location')
            parsed = urlparse.urlparse(url['href'])
            parse_qs(parsed.query)
            url_params = parse_qs(parsed.query)
            href = self.url_base+'pastadigital/abrirPastaProcessoDigital.do?nuProcesso='+url_params['processo.codigo'][0]+'&processo.foro='+url_params['processo.foro'][0]

        if multipla_janela:
            self.driver.find_element_by_id('pbVisualizarAutos').click()
        else:
            self.driver.execute_script("window.open('" + href + "', '_blank')")

        botaoFecharPopupSenha = self.driver.find_element_by_id('botaoFecharPopupSenha')
        if botaoFecharPopupSenha and botaoFecharPopupSenha.is_displayed():
            raise CriticalException("Sessão encerrada", self.uf, self.plataforma, self.prc_id, False)

        if multipla_janela:
            self.alterna_janela(2,2)
        else:
            self.alterna_janela()

        msg_erro = self.driver.find_element_by_id(self.id_mensagem_erro)
        if msg_erro and msg_erro.text.find('Não foi possível executar esta operação') > -1:
            if multipla_janela:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            return []

        doc_src = ''
        inicio = time.time()
        while not self.driver.find_element_by_id('arvore_principal'):
            time.sleep(0.5)
            if time.time() - inicio > 20:
                self.driver.refresh()

            if time.time() - inicio > 40:
                raise CriticalException("Erro ao carregar lista de arquivos", self.uf, self.plataforma, self.prc_id)

        self.driver.set_window_size(1200, 900)

        movimentos = self.driver.find_elements_by_xpath('//*[@id="arvore_principal"]/ul/li')
        movimentos.reverse()
        i_mov = len(movimentos)+1
        existe = False
        sem_data = []
        for mov in movimentos:
            i_mov -= 1
            if existe and len(pendentes) == 0:
                break

            pra_descricao = self.driver.find_element_by_xpath('//*[@id="arvore_principal"]/ul/li[' + str(i_mov) + ']/a').text.strip()
            # links = mov.find_elements_by_xpath('ul/li')
            links = self.driver.find_elements_by_xpath('//*[@id="arvore_principal"]/ul/li[' + str(i_mov) + ']/ul/li')
            links.reverse()
            i_li = len(links)+1
            for li in links:
                i_li -= 1
                arq = {}
                arq['pra_id_tj'] = self.driver.find_element_by_xpath('//*[@id="arvore_principal"]/ul/li[' + str(i_mov) + ']/ul/li[' + str(i_li) + ']').text.strip()
                el = self.driver.find_element_by_xpath('//*[@id="arvore_principal"]/ul/li['+str(i_mov)+']/ul/li['+str(i_li)+']')
                li_id = el.get_attribute('id')
                if li_id.find('midia') > -1:
                    r = re.findall("([0-9]{14})", arq['pra_id_tj'], re.IGNORECASE | re.DOTALL)
                    if len(r) > 0:
                        arq['pra_id_tj'] = r[0]
                    else:
                        arq['pra_id_tj'] = arq['pra_id_tj'][:29]

                arq['pra_prc_id'] = prc_id
                arq['pra_tentativas'] = None
                arq['pra_grau'] = self.grau
                arq['pra_plt_id'] = self.plataforma
                arq['pra_descricao'] = pra_descricao
                arq['pra_excluido'] = False
                arq['pra_erro'] = True

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

                erro_midia = False
                # SE NÃO FOR PARA FAZER DOWNLOAD, SALVA SOMENTE NA BASE, E MARCA COMO ERRO, PARA REALIZAR O DOWNLOAD POSTERIORMENTE
                if self.tipo != 2:
                    # li.click()
                    element = self.driver.find_element_by_xpath('//*[@id="arvore_principal"]/ul/li[' + str(i_mov) + ']/ul/li[' + str(i_li) + ']')
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center', inline: 'center'})", element)
                    li_id = element.get_attribute('id')
                    jan_adicional = False
                    if li_id.find('midia') > -1:
                        tit = element.text
                        self.driver.find_element_by_xpath('//*[@id="arvore_principal"]/ul/li[' + str(i_mov) + ']/ul/li[' + str(i_li) + ']/a').click()

                        arq['pra_usuario'] = None
                        arq['pra_erro'] = False
                        arq['pra_data'] = None
                        arq['pra_excluido'] = False
                        mr = self.driver.find_element_by_id('mensagemRetorno')
                        if mr:
                            if find_string(mr.text,('Não foi possível executar','Arquivo da audiência não encontrado')):
                                arq['pra_erro'] = True
                                erro_midia = True
                                self.driver.execute_script('window.history.back();')

                        r = re.findall("([0-9]{14})", tit, re.IGNORECASE | re.DOTALL)
                        if len(r) > 0:
                            dia = r[0]
                            try:
                                arq['pra_data'] = datetime.strptime(dia, '%Y%m%d%H%M%S')
                            except:
                                arq['pra_data'] = None
                        else:
                            sem_data.append(len(arquivos))

                        if not arq['pra_erro']:
                            result_download = aguarda_download(self.pasta_download, 1, tempo=360, tempo_nao_iniciado=45)
                            arq['pra_erro'] = not result_download
                    else:
                        self.driver.execute_script("$('#arvore_principal').jstree(true).select_node('" + li_id + "');", element)

                        self.driver.switch_to.default_content()
                        inicio = time.time()
                        while True:
                            self.driver.switch_to.frame(self.driver.find_element_by_id('documento'))
                            if time.time() - inicio > 60:
                                raise MildException("Erro ao carregar visualizador de arquivos " + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)

                            try:
                                wait = WebDriverWait(self.driver, 1)
                                wait.until(EC.visibility_of_element_located((By.ID, 'loadingBar')))
                            except:
                                pass

                            # try:
                            #     wait = WebDriverWait(self.driver, 20)
                            #     wait.until(EC.invisibility_of_element_located((By.ID, 'loadingBar')))
                            # except:
                            #     pass

                            old_style = ''
                            inicio = time.time()
                            while True:
                                if time.time() - inicio > 20:
                                    raise MildException("Page Loading Timeout", self.uf, self.plataforma, self.prc_id)

                                loadingBar = self.driver.find_element_by_id('loadingBar')
                                if not loadingBar:
                                    break

                                try:
                                    if not loadingBar.is_displayed():
                                        break
                                except:
                                    loadingBar = self.driver.find_element_by_id('loadingBar')

                                try:
                                    style = loadingBar.find_element_by_class_name('progress').get_attribute('style')
                                    if style != old_style:
                                        old_style = style
                                        inicio = time.time()
                                        continue
                                except:
                                    continue

                                if self.driver.find_element_by_id("errorMessage"):
                                    if self.driver.find_element_by_id("errorMessage").is_displayed():
                                        break

                            try:
                                wait = WebDriverWait(self.driver, 20)
                                wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'page')))
                            except:
                                if self.check_doc_error():
                                    arq['pra_excluido'] = True
                                    arq['pra_erro'] = False
                                    break

                                if not arq['pra_excluido']:
                                    if self.driver.find_element_by_id("mensagemRetorno"):
                                        print('erro RTF')
                                        if self.driver.find_element_by_id("mensagemRetorno").text.find('formato RTF') > -1:
                                            break
                                        else:
                                            raise MildException("Erro vis. arquivo" + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)
                                    else:
                                        tb = traceback.format_exc()
                                        print(tb)
                                        print('Tentando abrir arquivo')
                                        self.driver.refresh()
                                        self.driver.switch_to.default_content()
                                        element = self.driver.find_element_by_xpath('//*[@id="arvore_principal"]/ul/li[' + str(i_mov) + ']/ul/li[' + str(i_li) + ']')
                                        try:
                                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center', inline: 'center'})", element)
                                        except:
                                            time.sleep(2)
                                            try:
                                                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center', inline: 'center'})", element)
                                            except:
                                                raise MildException('erro ao chamar JS', self.uf, self.plataforma, self.prc_id)

                                        self.driver.find_element_by_xpath('//*[@id="arvore_principal"]/ul/li[' + str(i_mov) + ']/ul/li[' + str(i_li) + ']/a').click()
                                        foca_janela(self.process_children)
                                        continue

                            try:
                                wait = WebDriverWait(self.driver, 1)
                                wait.until(EC.visibility_of_element_located((By.ID, 'loadingBar')))
                            except:
                                pass
                            
                            try:
                                wait = WebDriverWait(self.driver, 20)
                                wait.until(EC.invisibility_of_element_located((By.ID, 'loadingBar')))
                            except:
                                pass
                            temp_doc_src = self.driver.find_element_by_class_name('page')
                            # print('temp_doc_src: ', temp_doc_src)
                            if doc_src == temp_doc_src:
                                print('documento igual, aguardando...')
                                # print('src:', doc_src, temp_doc_src)
                                self.driver.switch_to.default_content()
                                self.driver.execute_script("$('#arvore_principal').jstree(true).select_node('" + li_id + "');", element)
                                time.sleep(3)
                                self.driver.switch_to.frame(self.driver.find_element_by_id('documento'))
                                temp_doc_src = self.driver.find_element_by_class_name('page')
                                if doc_src == temp_doc_src:
                                    print('documento igual')
                                    self.driver.refresh()
                                    self.driver.switch_to.default_content()
                                    element = self.driver.find_element_by_xpath('//*[@id="arvore_principal"]/ul/li[' + str(i_mov) + ']/ul/li[' + str(i_li) + ']')
                                    time.sleep(1)
                                    try:
                                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center', inline: 'center'})", element)
                                    except:
                                        pass
                                    try:
                                        self.driver.execute_script("$('#arvore_principal').jstree(true).select_node('" + li_id + "');", element)
                                    except:
                                        raise MildException("Erro ao chamar JS ao abrir árvore", self.uf, self.plataforma, self.prc_id)

                                    continue

                            break
                        self.driver.switch_to.default_content()

                        if not arq['pra_excluido']:
                            inicio = time.time()
                            self.driver.execute_script("document.getElementById('divAssinaturas').style.display = 'block';")
                            cabecalho = self.driver.find_element_by_xpath('//*[@id="regiaoAssinatura"]/tbody/tr[2]/td/table/tbody/tr/td[2]/div/table/tbody/tr[2]/td')
                            cabecalho_txt = ''
                            jan_adicional = False
                            arq['pra_erro'] = False
                            while not cabecalho or cabecalho_txt == '':
                                if time.time() - inicio > 60:
                                    arq['pra_erro'] = True
                                    break
                                    # raise MildException("Erro ao carregar cabeçalho" + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)
                                if check_text(self.driver, '//*[@id="regiaoAssinatura"]/tbody/tr/td', 'conferência de documento digital'):
                                    self.driver.find_element_by_id('linkDocOriginal').click()
                                    self.alterna_janela(2,2)
                                    if self.driver.find_element_by_id("mensagemRetorno"):
                                        self.driver.close()
                                        self.alterna_janela(1, 3)
                                        arq['pra_excluido'] = True
                                        # arq['pra_erro'] = True
                                        break
                                    else:
                                        jan_adicional = True


                                    # if jan_adicional:
                                    #     wh = self.driver.window_handles
                                    #     if len(wh) > 2:
                                    #         self.driver.close()
                                    #     self.driver.switch_to.window(self.driver.window_handles[1])

                                try:
                                    self.driver.execute_script("document.getElementById('divAssinaturas').style.display = 'block';")
                                    cabecalho = self.driver.find_element_by_xpath('//*[@id="regiaoAssinatura"]/tbody/tr[2]/td/table/tbody/tr/td[2]/div/table/tbody/tr[2]/td')
                                    if cabecalho:
                                        cabecalho_txt = cabecalho.text
                                except:
                                    continue

                        if not arq['pra_erro'] and not arq['pra_excluido']:
                            cabecalho = cabecalho_txt

                            f = cabecalho.find(' em ')
                            pra_data = cabecalho[f+4:f + 23].replace('às ', '').strip()
                            f = cabecalho.find(' por ')
                            pra_usuario = cabecalho[f+4:-1].strip()

                            arq['pra_data'] = datetime.strptime(pra_data, '%d/%m/%Y %H:%M')
                            arq['pra_usuario'] = pra_usuario
                            self.driver.switch_to.frame(self.driver.find_element_by_id('documento'))

                            if self.driver.find_element_by_id("mensagemRetorno"):
                                self.driver.find_element_by_xpath('//*[@id="mensagemRetorno"]/li/a').click()
                            else:
                                inicio = time.time()
                                while not self.driver.find_element_by_class_name('page'):
                                    if self.check_doc_error():
                                        arq['pra_excluido'] = True
                                        arq['pra_erro'] = False
                                        break

                                    if time.time() - inicio > 60:
                                        raise MildException("Erro ao carregar pagina do documento " + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)
                                    time.sleep(0.2)
                                    if time.time() - inicio > 10:
                                        if jan_adicional:
                                            self.driver.refresh()
                                        else:
                                            self.driver.switch_to.default_content()
                                            # li.click()
                                            self.driver.find_element_by_xpath('//*[@id="arvore_principal"]/ul/li[' + str(i_mov) + ']/ul/li[' + str(i_li) + ']').click()
                                        self.driver.switch_to.frame(self.driver.find_element_by_id('documento'))
                                        aguarda_presenca_elemento(self.driver, '//*[@id="viewer"]/div[1]')

                                if not arq['pra_excluido']:
                                    inicio = time.time()
                                    while not self.driver.find_element_by_class_name('page'):
                                        time.sleep(0.2)
                                        if time.time() - inicio > 10:
                                            raise MildException('erro download (ao abrir documento)' + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)

                                    inicio = time.time()
                                    total = len(self.driver.find_elements_by_id('download'))
                                    while total == 0:
                                        total = len(self.driver.find_elements_by_id('download'))
                                        print('tentando localizar botão download')
                                        time.sleep(0.2)
                                        if time.time() - inicio > 10:
                                            raise MildException('erro ao localizar botão download' + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)

                                    try:
                                        self.driver.find_element_by_id('download').click()
                                    except:
                                        time.sleep(1)
                                        foca_janela(self.process_children)
                                        self.driver.find_element_by_id('download').click()

                            if not arq['pra_excluido']:
                                inicio = time.time()
                                result_download = aguarda_download(self.pasta_download, 1, tempo=180, tempo_nao_iniciado=30)

                                # CONFERE SE O ESAJ NÃO TENTOU IMPRIMIR AUTOMATICAMENTE
                                auto_print = False
                                if not result_download and self.driver.find_element_by_xpath('//*[@id="printServiceOverlay"]/div/div[2]/span'):
                                    print('falha no download... verificando impressão')
                                    pc = self.driver.find_element_by_xpath('//*[@id="printServiceOverlay"]/div/div[2]/progress').get_attribute('value')
                                    # print('pc:',pc)
                                    if pc == '100':
                                        auto_print = True

                                if (not result_download and time.time() - inicio < 50) or auto_print:
                                    print('tentando baixar novamente')
                                    foca_janela(self.process_children)
                                    webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                                    time.sleep(1)
                                    limpar_pasta(self.pasta_download)
                                    self.driver.find_element_by_id('download').click()
                                    result_download = aguarda_download(self.pasta_download, 1, tempo=180, tempo_nao_iniciado=60)

                                arq['pra_erro'] = not result_download

                    if not arq['pra_excluido']:
                        doc_src = self.driver.find_element_by_class_name('page')
                    if jan_adicional:
                        wh = self.driver.window_handles
                        if len(wh) > 2:
                            self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[1])

                    if erro_midia:
                        arq['pra_excluido'] = True
                        arq['pra_erro'] = False

                    if not arq['pra_erro']:
                        if arq['pra_excluido']:
                            arq['pra_original'] = None
                            arq['pra_arquivo'] = None
                            arq['pra_usuario'] = None
                            arq['pra_data'] = None
                        else:
                            total_arquivos += 1
                            file_names = os.listdir(self.pasta_download)
                            arq['pra_original'] = file_names[0]
                            pra_arquivo = trata_arquivo(file_names[0], self.pasta_download, pasta_intermediaria)
                            arq['pra_arquivo'] = pra_arquivo
                    elif self.tipo != 2:
                        webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                        arq['pra_original'] = None
                        arq['pra_arquivo'] = None
                        arq['pra_usuario'] = None
                        arq['pra_data'] = None
                        arq['pra_tentativas'] = 1 if arq['pra_tentativas'] is None else arq['pra_tentativas'] + 1
                        limpar_pasta(self.pasta_download)
                        if not erro_midia:
                            # print('erro download')
                            # time.sleep(9999)
                            raise MildException('erro download ' + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)

                    self.driver.switch_to.default_content()

                arq['pra_data_insert'] = datetime.now()
                arquivos.append(arq)

        wh = self.driver.window_handles
        if len(wh) > 1:
            self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

        for s in sem_data:
            if 'pra_id' not in arquivos[s]:
                i=0
                while s+i < len(arquivos):
                    i += 1
                    if len(arquivos) > s + i and arquivos[s + i]['pra_data'] is not None:
                        arquivos[s]['pra_data'] = arquivos[s + i]['pra_data']
                        break
                    elif s-i > 0 and arquivos[s - i]['pra_data'] is not None:
                        arquivos[s]['pra_data'] = arquivos[s - i]['pra_data']
                        break

        arquivos.reverse()
        if multipla_janela:
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
        return arquivos

    def check_doc_error(self):
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(self.driver.find_element_by_id('documento'))
        if self.driver.find_element_by_id("errorMessage"):
            txt = self.driver.find_element_by_id("errorMessage").text
            if find_string(txt, ('Arquivo PDF corrompido', 'Ocorreu um erro ao carregar')):
                return True

        return False

    # FECHA A JANELA DO PROCESSO ABERTO ATUALMENTE
    def fecha_processo(self):
        wh = self.driver.window_handles
        while len(wh) > 1:
            try:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.close()
                wh = self.driver.window_handles
            except:
                pass

        self.driver.switch_to.window(self.driver.window_handles[0])

