import time

from Controllers.Tribunais.Ppe._ppe import *
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
import urllib.parse as urlparse
from urllib.parse import parse_qs

# CLASSE DA VARREDURA DO EPROC DO RJ. HERDA OS METODOS DA CLASSE EPROC
class RJ(Ppe):
    def __init__(self):
        super().__init__()
        self.movs = []
        self.tratar_tamanhos = False
        # self.pagina_inicial = "https://www3.tjrj.jus.br/segweb/faces/login.jsp?indGet=true&SIGLASISTEMA=PORTALSERV"
        self.pagina_inicial = "https://www3.tjrj.jus.br/segweb/faces/login.jsp?indGet=true&SIGLASISTEMA=PORTALSERVICOS"
        # self.pagina_busca = 'http://www4.tjrj.jus.br/ConsultaUnificada/consulta.do#tabs-numero-indice0'
        self.pagina_busca = 'https://www3.tjrj.jus.br/portalservicos/#/consproc/consultaportal'
        # self.pagina_processo = 'http://www4.tjrj.jus.br/consultaProcessoWebV2/consultaMov.do?v=2&acessoIP=internet&tipoUsuario=&numProcesso='
        self.reiniciar_navegador = False
        self.pesquisado = False

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc):
        adc = self.audiencias()
        status_atual = 'Ativo' if self.completo else proc['prc_status']
        prt = self.partes()
        adv = self.responsaveis()
        prc = self.dados(status_atual)

        return adc, prt, prc, adv

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''
        if not aguarda_presenca_elemento(self.driver, 'txtLogin', tipo='ID'):
            return False

        self.driver.find_element_by_id("txtLogin").send_keys(usuario)
        self.driver.find_element_by_id("txtSenha").send_keys(senha)
        self.driver.find_element_by_id("txtSenha").send_keys(Keys.ENTER)

        if not aguarda_presenca_elemento(self.driver, 'portlet_com_liferay_journal_content_web_portlet_JournalContentPortlet_INSTANCE_hP5T', tipo='ID'):
            return False

        wh = self.driver.window_handles
        while len(wh) == 1:
            wh = self.driver.window_handles

        self.alterna_janela()
        self.driver.find_element_by_xpath('//*[@id="dropdownPerfil"]/div/div[1]/div[1]/input').send_keys('Advogado')
        time.sleep(0.5)
        self.driver.find_element_by_xpath('//*[@id="dropdownPerfil"]/div/div[1]/div[1]/input').send_keys(Keys.DOWN)
        self.driver.find_element_by_xpath('//*[@id="dropdownPerfil"]/div/div[1]/div[1]/input').send_keys(Keys.ENTER)
        time.sleep(1)
        self.driver.find_element_by_xpath('//*[@id="dropdownPerfil"]/div/div[1]/div[1]/input').send_keys(Keys.TAB)
        self.driver.find_element_by_xpath('//*[@id="corpo"]/app-trocar-perfil/div[2]/div/div/div[2]/a[1]').send_keys(Keys.ENTER)

        # self.set_config()

        # href = 'http://www4.tjrj.jus.br/ConsultaUnificada/consulta.do#tabs-numero-indice0'
        # self.driver.execute_script("window.open('" + href + "', '_blank')")
        # self.alterna_janela(2,2)

        return True

    # LISTA PROCESSOS NA PAGINA INICIAL
    def set_config(self):
        self.driver.switch_to.window(self.driver.window_handles[1])
        if not self.pesquisado:
            self.pesquisado = True
            self.driver.execute_script('winFiltroProcessosOAB.show(); storeComarca.load();')
            origem = self.driver.find_element_by_id('comboOrigem')
            origem.send_keys('Todas')

            ano_inicial = self.driver.find_element_by_id('txtAnoInicial')
            ano_inicial.clear()
            ano_inicial.send_keys('2021')

            time.sleep(2)
            self.driver.find_element_by_id('ext-comp-1122').click()
            aguarda_presenca_elemento(self.driver, '//*[@id="idGridConsultaOAB"]/div[2]/div[1]/div/div/div[2]/div/div[1]/div[2]/div/div[1]/table')

        actionChains = ActionChains(self.driver)
        actionChains.double_click(self.driver.find_element_by_xpath('//*[@id="idGridConsultaOAB"]/div[2]/div[1]/div/div/div[2]/div/div[1]/div[2]/div/div[1]/table')).perform()
        time.sleep(2)
        if not try_click(self.driver,'//*[@id="portalTabs"]/div[1]/div[1]/ul/li[2]/a[1]'):
            time.sleep(5)
            self.driver.find_element_by_xpath('//*[@id="portalTabs"]/div[1]/div[1]/ul/li[2]/a[1]').click()
        return

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''

        # try:
        #     field = self.driver.find_element_by_id('parte1ProcCNJ')
        #     field.clear()
        # except:
        #     self.driver.get(self.pagina_busca)
        #     field = self.driver.find_element_by_id('parte1ProcCNJ')
        #     field.clear()
        # time.sleep(2)
        if not aguarda_presenca_elemento(self.driver,'//*[@id="corpo"]/app-iframe/section/iframe', tempo=30):
            raise MildException("Erro ao carregar página de busca", self.uf, self.plataforma, self.prc_id, False)

        iframe_processo = self.driver.find_element_by_xpath('//*[@id="corpo"]/app-iframe/section/iframe')
        self.driver.switch_to_frame(iframe_processo)

        if not aguarda_presenca_elemento(self.driver,'//*[@id="porNumero"]/div[1]/div/app-codigo-processo-origem/div/div[2]/div/div/input[1]', tempo=45):
            raise MildException("Erro ao carregar página de busca", self.uf, self.plataforma, self.prc_id, False)

        self.wait_load()
        field = self.driver.find_element_by_xpath('//*[@id="porNumero"]/div[1]/div/app-codigo-processo-origem/div/div[2]/div/div/input[1]')
        field.send_keys(numero_busca[:-7])

        field = self.driver.find_element_by_id('inputSufixoUnica3')
        field.clear()
        field.send_keys(numero_busca[-4:])

        self.driver.find_element_by_id('botaoPesquisarProcesso').click()
        time.sleep(1)

        self.wait_load()

        erro = self.driver.find_element_by_xpath('/html/body/app-root/simple-notifications/div/simple-notification/div/div[1]/div')
        if erro:
            if erro.text.find('inválido'):
                return False

        # if aguarda_alerta(self.driver, tempo=1, aceitar=True):
        #     return False

        # captcha = self.driver.find_element_by_id('imgCaptcha')
        # if captcha:
        #     self.set_config()
        #     raise MildException("Captcha Solicitado", self.uf, self.plataforma, self.prc_id)

        return True

    # LOCALIZA RECURSOS E INSERE NA BASE
    def insert_recursos(self, base, proc):
        rels = self.driver.find_elements_by_xpath('//*[@id="content"]/form/table/tbody/tr')
        achei = False

        for rel in rels:
            if len(rel.find_elements_by_xpath('td[2]')) == 0:
                continue

            td1 = rel.find_element_by_xpath('td[1]').text
            chaves = ('Processo(s) no Tribunal de Justiça:','Processo(s) no Conselho Recursal:')
            if find_string(td1, chaves):
                links = rel.find_elements_by_xpath('td[2]/a')
                for link in links:
                    rec_numero = link.text
                    rec_url = link.get_attribute('href')
                    if rec_url.find('?N=') == -1:
                        continue

                    parsed = urlparse.urlparse(rec_url)
                    parse_qs(parsed.query)
                    url_params = parse_qs(parsed.query)
                    rec_codigo = url_params['N'][0]

                    result = Recurso.select(base, proc['prc_id'], rec_codigo=rec_codigo)
                    if len(result) == 0:
                        Recurso.insert(base, {'rec_prc_id': proc['prc_id'], 'rec_numero': rec_numero, 'rec_codigo': rec_codigo, 'rec_plt_id': self.plataforma})
                        achei = True

            chaves = ('Processo(s) Apensado(s):',)
            if find_string(td1, chaves):
                links = rel.find_elements_by_xpath('td[2]/a')
                for link in links:
                    prc_numero = link.text
                    prc_url = link.get_attribute('href')
                    if prc_url.find('numProcesso=') == -1:
                        continue

                    parsed = urlparse.urlparse(prc_url)
                    parse_qs(parsed.query)
                    url_params = parse_qs(parsed.query)
                    prc_codigo = url_params['numProcesso'][0]

                    if not Processo.processo_existe(base, prc_numero):
                        print("inserindo processo anexo")
                        np = [{'prc_numero': prc_numero, 'prc_estado': self.uf, 'prc_autor': proc['prc_autor'], 'prc_pai': proc['prc_id'], 'prc_area': 1, 'prc_carteira': proc['prc_carteira'],'prc_codido': prc_codigo}]
                        Processo.insert(base, np)
                        achei = True
        return achei

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''

        # nao_humano = self.driver.find_element_by_xpath('//*[@id="conteudo"]/h3')
        # if nao_humano:
        #     if nao_humano.text.find('Interação não humana detectada'):
        #         print('Interação não humana detectada')
        #         self.driver.execute_script("history.back(); return false")
        #         time.sleep(10)
        #         self.set_config()
        #         raise MildException("Interação não humana detectada", self.uf, self.plataforma, self.prc_id)
        iframe_processo = self.driver.find_element_by_xpath('//*[@id="corpo"]/app-iframe/section/iframe')
        if iframe_processo:
            self.driver.switch_to_frame(iframe_processo)

        self.wait_load()
        n = self.driver.find_element_by_xpath('//*[@id="pdf"]/div/div[2]/div[2]/div[1]')
        if not n:
            raise MildException("Captcha Solicitado", self.uf, self.plataforma, self.prc_id)

        n = n.text
        n1 = localiza_cnj(n)
        n1 = ajusta_numero(n1)
        if n1 != numero_busca:
            raise MildException("CNJ diferente na busca", self.uf, self.plataforma, self.prc_id, False)

        return True

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):

        while True:
            if self.driver.find_elements_by_xpath('//*[@id="porNumero"]/div[3]/div/p-table/div/div/table/tbody/tr/td[1]/a'):
                break

            if self.driver.find_elements_by_xpath('//*[@id="pdf"]/div/div[2]/div[2]/div[1]'):
                break


        links = self.driver.find_elements_by_xpath('//*[@id="porNumero"]/div[3]/div/p-table/div/div/table/tbody/tr/td[1]/a')
        for link in links:
            rec_url = link.find_elements_by_xpath('span').strip()
            rec_url = rec_url.replace('(','').replace(')','').strip()
            print('rec_url', rec_url)
            if rec_url == codigo:
                link.click()
                break

        self.wait_load()
        self.confere_cnj(numero_busca)

        return False

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''

        acp_cadastro = None
        acp_esp = ''
        acp_tipo = ''
        movimentos = self.driver.find_elements_by_xpath('//*[@id="content"]/form/table/tbody/tr')
        if len(movimentos) == 0:
            movimentos = self.driver.find_elements_by_xpath('//*[@id="conteudo"]/span/table/tbody/tr')

        novo = False


        while True:
            if len(movimentos) == 0:
                break
            if movimentos[-1].text.strip() == '':
                del movimentos[-1]
            else:
                break

        x = 0
        for linha in movimentos:
            x += 1
            if len(linha.find_elements_by_xpath('td[2]')) == 0:
                continue

            td1 = linha.find_element_by_xpath('td[1]').text
            chaves = ('Tipo do Movimento', 'FASE ATUAL:', 'FASE:', 'Processo(s) no Conselho Recursal',
                      'Processo(s) no Tribunal de Justiça:', 'PUBLICAÇÃO DO ACÓRDÃO', 'INTEIRO TEOR',
                      'SESSAO DE JULGAMENTO',)
            if find_string(td1, chaves) or len(movimentos) == x:
                novo = True
                if acp_cadastro is not None:
                    if acp_esp.strip() == '':
                        acp_esp = acp_tipo
                    else:
                        acp_esp = acp_esp.replace('Ver íntegra do(a) Despacho', '').replace('  ', ' ')

                    acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp.strip(), 'acp_tipo': acp_tipo}

                    break

                acp_cadastro = None
                acp_tipo = linha.find_element_by_xpath('td[2]').text
                acp_esp = ''

                if find_string(td1, chaves[3:]) or len(movimentos) == x:
                    break

                continue

            # if 'Data' in linha.find_element_by_xpath('td[1]').text:
            if novo:
                try:
                    acp_cadastro = linha.find_element_by_xpath('td[2]').text
                    if len(acp_cadastro) < 12:
                        acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y')
                    else:
                        acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y %H:%M')
                    novo = False
                except:
                    acp_esp += linha.find_element_by_xpath('td[1]').text + ' ' + linha.find_element_by_xpath('td[2]').text + ' '
                continue

            td1 = linha.find_element_by_xpath('td[1]').text.strip()
            if td1 == '':
                continue
            td2 = linha.find_element_by_xpath('td[2]').text.strip()
            acp_esp += td1 + ' ' + td2 + ' '

        return Acompanhamento.compara_mov(base, prc_id, acp_esp.strip(), acp_cadastro, self.plataforma, self.grau, rec_id=self.rec_id)

    # CAPTURA ACOMPANHAMENTOS DO PROCESSO
    def acompanhamentos(self, proc_data, completo, base):
        '''
        :param datetime Última movimentação registrada na base
        :param bool Realiza a captura completa das movimentações
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        print('acps')
        prc_id = proc_data['prc_id']
        rec_id = proc_data['rec_id'] if 'rec_id' in proc_data else None
        movs = []
        self.movs = []

        if self.grau == 1:
            self.insert_recursos(base, proc_data)

        lista = Acompanhamento.lista_movs(base, prc_id, self.plataforma, acp_grau=self.grau, rec_id=rec_id)

        btn = self.driver.find_element_by_xpath('//*[@id="pdf"]/div/div[1]/div[2]/button[2]')
        if btn:
            btn.click()
            while True:
                if self.driver.find_elements_by_xpath('//*[@id="movimentacaoProcessoC"]/div[1]/div[2]'):
                    break

        capturar = True
        i = 0
        while True:
            if not capturar:
                break

            mov = {}
            movimentos = self.driver.find_elements_by_xpath('//*[@id="movimentacaoProcessoC"]/div[1]/div')
            for movimento in movimentos:
                i += 1
                acp_cadastro = movimento.find_element_by_xpath('app-movimento/div[2]/div[1]/label[2]').text
                mov['acp_cadastro'] = datetime.strptime(acp_cadastro, '%d/%m/%Y')
                acp_tipo = movimento.find_element_by_xpath('app-movimento/div[1]').text
                mov['acp_tipo'] = acp_tipo.replace('Tipo do Movimento:').strip()

                for l in lista:
                    tipo_base = corta_string(l['acp_tipo'])
                    if acp_cadastro == l['acp_cadastro'] and acp_tipo.upper().strip() == tipo_base.upper().strip():
                        capturar = False
                        break

                if not capturar:
                    break

                if not capturar and not completo and i >= 10:
                    break

                acp_esp = ''
                esps = movimento.find_element_by_xpath('app-movimento/div/div[1]')
                del esps[0]
                for esp in esps:
                    acp_esp += ' ' + esp.text

                mov['acp_esp'] = acp_esp.strip()

                if capturar:
                    movs.append(mov)

                self.movs.append({**mov, 'novo': capturar})

            btn_prox = self.driver.find_elements_by_xpath('//*[@id="movimentacaoProcessoC"]/div[1]/div[12]/p-paginator/div/button[3]')
            if not btn_prox:
                break

            btn_prox.click()

        return movs

    # CAPTURA AUDIENCIAS DO PROCESSO
    def audiencias(self):
        adcs = []
        for mov in self.movs:
            if not self.completo and not mov['novo']:
                break

            esp = mov['acp_esp'].upper().strip()
            tipo = mov['acp_tipo'].upper().strip()

            esp = esp.replace('Descrição:','').strip()

            if esp.find('AUDIÊNCIA') != 0 and tipo.find('AUDIÊNCIA') != 0:
                continue

            esp = esp.replace('H:',':')
            aud = localiza_audiencia(esp, formato_data='%d/%m/%Y %H:%M', formato_re='(\\d+)(\\/)(\\d+)(\\/)(\\d+)(\\s+)(ÀS)(\\s+)(\\d+)(\\:)(\\d+)', reverse=True)
            if not aud:
                continue

            erro = ''
            if 'prp_status' not in aud:
                erro = 'Status '
            if 'prp_tipo' not in aud:
                erro = 'Tipo '

            if erro != '':
                raise MildException("Audiência - "+erro+" não localizado: "+esp, self.uf, self.plataforma, self.prc_id)

            aud['data_mov'] = mov['acp_cadastro']
            adcs.append(aud)

        return adcs

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        prts = {'ativo':[], 'passivo':[], 'terceiro':[]}

        popup = True
        autor = True

        link = self.driver.find_element_by_link_text('Listar todos os personagens')
        if link:
            link.click()
        else:
            popup = False
            autor = False
            partes = self.driver.find_elements_by_xpath('//*[@id="content"]/form/table/tbody/tr')


        for parte in partes:
            if len(parte.find_elements_by_xpath('td[2]')) == 0:
                continue

            tipo = parte.find_element_by_xpath('td[1]').text.strip()

            if not popup and (tipo.upper().find('ADVOGAD') > -1 and tipo.upper().find('AVISO AO ADVOGADO') == -1):
                break

            if not autor:
                if tipo.upper().find('AUTOR') > -1 or tipo.upper().find('REQUERENTE') > -1:
                    autor = True
                else:
                    continue

            if tipo == '':
                continue
            if find_string(tipo,self.titulo_partes['ignorar']):
                continue

            polo = ''
            if find_string(tipo,self.titulo_partes['ativo']):
                polo = 'ativo'
            if find_string(tipo,self.titulo_partes['passivo']):
                polo = 'passivo'
            if find_string(tipo,self.titulo_partes['terceiro']):
                polo = 'terceiro'

            if polo == '':
                # print("polo vazio ", tipo, polo)
                # time.sleep(9999)
                raise MildException("polo vazio "+tipo, self.uf, self.plataforma, self.prc_id)

            prr_nome = parte.find_element_by_xpath('td[2]').text
            prts[polo].append({'prt_nome': prr_nome, 'prt_cpf_cnpj': 'Não Informado'})

        # if len(prts['ativo']) == 0:
        #     print(prts)
        #     raise MildException("partes vazia ", self.uf, self.plataforma, self.prc_id)
        return prts

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []

        link = self.driver.find_element_by_link_text('Listar todos os personagens')
        if link:
            partes = self.driver.find_elements_by_xpath('//*[@id="listaPersonagens"]/table/tbody/tr')
            if len(partes) > 0:
                partes.pop(0)
                polo = ''
                for parte in partes:
                    tipo = parte.find_element_by_xpath('td[1]').text
                    if tipo.upper().find('ADVOGAD') == -1 and find_string(tipo,self.titulo_partes['ignorar']):
                        continue
                    if find_string(tipo,self.titulo_partes['terceiro']):
                        continue


                    if find_string(tipo,self.titulo_partes['ativo']):
                        polo = 'Polo Ativo'
                        continue
                    if find_string(tipo,self.titulo_partes['passivo']):
                        polo = 'Polo Passivo'
                        continue

                    if polo == '':
                        # print("polo vazio "+tipo)
                        # time.sleep(999)
                        raise MildException("polo vazio "+tipo, self.uf, self.plataforma, self.prc_id)

                    if tipo.upper().find('ADVOGAD') == -1:
                        continue

                    advogados = parte.find_element_by_xpath('td[2]').text
                    f = advogados.find(')')
                    prr_oab = advogados[1:f].strip()
                    prr_nome = advogados[f+1:].strip()

                    resps.append({'prr_nome': prr_nome, 'prr_oab': prr_oab, 'prr_cargo': 'Advogado', 'prr_parte': polo})

                self.driver.execute_script('javascript:exibeListaPersonagens();')

        return resps

     # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        '''
        :param str status_atual: Status atual
        '''
        prc = {}
        prc['prc_status'] = get_status(self.movs, status_atual, somente_tipo=True)
        n = self.driver.find_element_by_xpath('//*[@id="pdf"]/div/div[2]/div[2]/div[1]')
        prc['prc_numero2'] = localiza_cnj(n.text)

        campos = {'Classe': 'prc_classe', 'Assunto': 'prc_assunto', 'Comarca': 'prc_comarca2', }

        # url = self.driver.execute_script('return window.location')
        # parsed = urlparse.urlparse(url['href'])
        # parse_qs(parsed.query)
        # url_params = parse_qs(parsed.query)
        # # print(url_params)
        # prc['prc_codigo'] = url_params['numProcesso'][0]

        linhas = self.driver.find_elements_by_xpath('//*[@id="pdf"]/div/div[2]/div[2]/div[6]/div/div/div')
        for linha in linhas:
            labels = linha.find_elements_by_xpath('label')
            if len(labels) < 2:
                continue

            titulo = labels[0].text
            conteudo = labels[1].text
            for cmp in campos:
                if titulo.upper().find(cmp.upper()) > -1:
                    prc[campos[cmp]] = conteudo.strip()
                    break

        if 'prc_comarca2' in prc:
            prc['prc_juizo'] = prc['prc_comarca2']
            prc['prc_comarca2'] = localiza_comarca(prc['prc_comarca2'], 'RJ')

        return prc

    # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS
    def download(self, prc_id, arquivos_base, pendentes, target_dir):
        return []

    # FECHA A JANELA DO PROCESSO ABERTO ATUALMENTE
    def fecha_processo(self):
        self.driver.switch_to.window(self.driver.window_handles[-1])

    # AGUARDA ATÉ QUE A ANIMAÇÃO DE LOADING ESTEJA OCULTA
    def wait_load(self, tempo=30):
        if self.driver.find_element_by_id('//*[@id="loadingbox"]'):
            wait = WebDriverWait(self.driver, tempo)
            try:
                wait.until(EC.invisibility_of_element((By.ID, id)))
            except TimeoutException:
                raise MildException("Loading Timeout", self.uf, self.plataforma, self.prc_id, False)

        app_loading = self.driver.find_element_by_xpath('//*[@id="consultaConteudo"]/app-loading')
        if app_loading:
            inicio = time.time()
            while self.driver.find_element_by_xpath('//*[@id="consultaConteudo"]/app-loading/div'):
                time.sleep(0.2)
                if time.time() - inicio > tempo:
                    raise MildException("Loading Timeout", self.uf, self.plataforma, self.prc_id, False)

        return True

