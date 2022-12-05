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
        self.pagina_inicial = "https://www3.tjrj.jus.br/segweb/faces/login.jsp"
        # self.pagina_busca = 'http://www4.tjrj.jus.br/ConsultaUnificada/consulta.do#tabs-numero-indice0'
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

        # if not aguarda_presenca_elemento(self.driver, 'portlet_com_liferay_journal_content_web_portlet_JournalContentPortlet_INSTANCE_hP5T', tipo='ID'):
        if not aguarda_presenca_elemento(self.driver, 'cmbSistemas', tipo='ID'):
            return False

        select = Select(self.driver.find_element_by_id('cmbSistemas'))
        select.select_by_visible_text('PORTAL DE SERVIÇOS')
        self.driver.execute_script("TrPage._autoSubmit('_id5','cmdEnviar',event,1);")
        # self.driver.find_element_by_id("cmdEnviar").click()

        inicio = time.time()
        wh = self.driver.window_handles
        while len(wh) == 1:
            if time.time() - inicio > 45:
                raise MildException("Loading Timeout - Abrir Janela Login", self.uf, self.plataforma, self.prc_id, False)
            wh = self.driver.window_handles

        self.alterna_janela()
        aguarda_presenca_elemento(self.driver, '//*[@id="dropdownPerfil"]/div/div[1]/div[1]/input', tempo=60)
        self.driver.find_element_by_xpath('//*[@id="dropdownPerfil"]/div/div[1]/div[1]/input').send_keys('Advogado')
        time.sleep(1)
        self.driver.find_element_by_xpath('//*[@id="dropdownPerfil"]/div/div[1]/div[1]/input').send_keys(Keys.DOWN)
        self.driver.find_element_by_xpath('//*[@id="dropdownPerfil"]/div/div[1]/div[1]/input').send_keys(Keys.ENTER)
        time.sleep(1)
        self.driver.find_element_by_xpath('//*[@id="dropdownPerfil"]/div/div[1]/div[1]/input').send_keys(Keys.TAB)
        time.sleep(1)
        self.driver.find_element_by_xpath('//*[@id="corpo"]/app-trocar-perfil/div[2]/div/div/div[2]/a[1]').send_keys(Keys.ENTER)

        if not aguarda_presenca_elemento(self.driver, 'menu-lateral', tipo='ID', tempo=10):
            self.driver.find_element_by_xpath('//*[@id="corpo"]/app-trocar-perfil/div[2]/div/div/div[2]/a[1]').send_keys(Keys.ENTER)
        # self.set_config()

        # aguarda_presenca_elemento(self.driver, 'menu-lateral', tipo='ID')
        # if self.grau == 1:
        #     href = 'http://www4.tjrj.jus.br/ConsultaUnificada/consulta.do#tabs-numero-indice0'
        #     self.driver.execute_script("window.open('" + href + "', '_blank')")
        #     self.alterna_janela(2,2)
        # else:
        # self.driver.get('https://www3.tjrj.jus.br/portalservicos/#/consproc/consultaportal')
        aguarda_presenca_elemento(self.driver, 'CONSULTAS', tipo='ID')
        time.sleep(5)
        self.driver.execute_script("teste = document.getElementsByClassName('submenu-sidebar'); teste[5].click();")

        # for i in range(0, 50):
        #     self.driver.find_element_by_xpath('/html/body').send_keys(Keys.TAB)

        # self.driver.find_element_by_xpath('/html/body').send_keys(Keys.ENTER)
        # while True:
        #     try:
        #         self.driver.find_element_by_xpath('/html/body/app-root/app-layout/app-sidebar/nav/div/ul/li[6]/div').click()
        #         break
        #     except:
        #         pass
        time.sleep(1)
        self.driver.execute_script("teste = document.getElementsByClassName('btn-submenu'); teste[0].click();")

        # self.driver.find_element_by_xpath('//*[@id="corpo"]/app-menu-expandido/section/div/div[2]/div[1]').click()


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

        # self.driver.get('https://www3.tjrj.jus.br/portalservicos/#/consproc/consultaportal')
        if not aguarda_presenca_elemento(self.driver,'//*[@id="corpo"]/app-iframe/section/iframe', tempo=30):
            raise MildException("Erro ao carregar página de busca", self.uf, self.plataforma, self.prc_id, False)

        if not aguarda_presenca_elemento(self.driver,'//*[@id="corpo"]/app-iframe/section/iframe', tempo=30):
            raise MildException("Erro ao carregar página de busca", self.uf, self.plataforma, self.prc_id, False)

        iframe_processo = self.driver.find_element_by_xpath('//*[@id="corpo"]/app-iframe/section/iframe')
        self.driver.switch_to_frame(iframe_processo)


        titulo = self.driver.find_element_by_xpath('//*[@id="pdf"]/div/div[2]/div[2]/div[1]/div/span/b')
        if titulo:
            self.driver.execute_script('javascript:history.go(-1);')
        # try_click(self.driver, '//*[@id="content-barra"]/a[1]')

        if not aguarda_presenca_elemento(self.driver,'//*[@id="porNumero"]/div[1]/div/app-codigo-processo-origem/div/div[2]/div/div/input[1]', tempo=45):
            raise MildException("Erro ao carregar página de busca", self.uf, self.plataforma, self.prc_id, False)

        self.wait_load()
        field = self.driver.find_element_by_xpath('//*[@id="porNumero"]/div[1]/div/app-codigo-processo-origem/div/div[2]/div/div/input[1]')
        field.clear()
        field.send_keys(numero_busca[:-7])

        field = self.driver.find_element_by_id('inputSufixoUnica3')
        field.clear()
        field.send_keys(numero_busca[-4:])

        self.driver.execute_script("document.getElementById('botaoPesquisarProcesso').click();")
        # self.driver.find_element_by_id('botaoPesquisarProcesso').click()
        time.sleep(1)

        self.wait_load()

        erro = self.driver.find_element_by_xpath('/html/body/app-root/simple-notifications/div/simple-notification/div/div[1]/div')
        if erro:
            if erro.text.find('inválido'):
                return False

        modal_pje = self.driver.find_element_by_xpath('//*[@id="modal-aviso-pje"]/div/div/div/div[2]/p')
        if modal_pje:
            if modal_pje.text.find('um processo do PJE'):
                return False

        return True

    # LOCALIZA RECURSOS E INSERE NA BASE
    def insert_recursos(self, base, proc):
        achei = False
        divs = self.driver.find_element_by_xpath('//*[@id="pdf"]/div/div[2]/div[2]/div[6]')
        linhas = divs.find_elements_by_class_name('control-label')
        conts = divs.find_elements_by_class_name('form-dados-estaticos')
        i = -1
        for linha in linhas:
            i += 1

            titulo = linha.text
            chaves = ('Processo(s) no Tribunal de Justiça','Processo(s) no Conselho Recursal')
            if find_string(titulo, chaves):
                divs = conts[i].find_elements_by_tag_name('div')
                for div in divs:
                    rec_numero = div.text.strip()
                    if rec_numero == 'Não há':
                        continue

                    result = Recurso.select(base, proc['prc_id'], rec_numero=div.text.strip())
                    if len(result) == 0:
                        Recurso.insert(base, {'rec_prc_id': proc['prc_id'], 'rec_numero': rec_numero, 'rec_plt_id': self.plataforma})
                        achei = True

            chaves = ('Processo(s) Apensado(s):',)
            if find_string(titulo, chaves):
                divs = conts[i].find_elements_by_tag_name('div')
                for div in divs:
                    prc_numero = div.text.strip()
                    if not Processo.processo_existe(base, prc_numero):
                        print("inserindo processo anexo")
                        np = [{'prc_numero': prc_numero, 'prc_estado': self.uf, 'prc_autor': proc['prc_autor'],
                               'prc_pai': proc['prc_id'], 'prc_area': 1, 'prc_carteira': proc['prc_carteira'], }]
                        Processo.insert(base, np)
                        achei = True

        return achei


        rels = self.driver.find_elements_by_xpath('//*[@id="content"]/form/table/tbody/tr')


        for rel in rels:
            if len(rel.find_elements_by_xpath('td[2]')) == 0:
                continue

            td1 = rel.find_element_by_xpath('td[1]').text
            chaves = ('Processo(s) no Tribunal de Justiça','Processo(s) no Conselho Recursal')
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
        iframe_processo = self.driver.find_element_by_xpath('//*[@id="corpo"]/app-iframe/section/iframe')
        if iframe_processo:
            self.driver.switch_to_frame(iframe_processo)

        self.wait_load()
        if not aguarda_presenca_elemento(self.driver, '//*[@id="pdf"]/div/div[2]/div[2]/div[1]/div'):
            raise MildException("Erro ao carregar página do processo", self.uf, self.plataforma, self.prc_id)

        inicio = time.time()
        n = ''
        while n == '':
            if time.time() - inicio > 30:
                raise MildException("CNJ não localizado", self.uf, self.plataforma, self.prc_id)
            n = self.driver.find_element_by_xpath('//*[@id="pdf"]/div/div[2]/div[2]/div[1]/div').text
        # if not n:
        #     raise MildException("Captcha Solicitado", self.uf, self.plataforma, self.prc_id)

        # n = n.text
        n1 = localiza_cnj(n)
        n1 = ajusta_numero(n1)

        if n1 != numero_busca:
            raise MildException("CNJ diferente na busca", self.uf, self.plataforma, self.prc_id, False)

        return True

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):

        inicio = time.time()
        while True:
            if time.time() - inicio > 45:
                raise MildException("Timeout ao conferir segredo", self.uf, self.plataforma, self.prc_id)

            if self.driver.find_elements_by_xpath('//*[@id="porNumero"]/div[3]/div/p-table/div/div/table/tbody/tr/td[1]/a'):
                break

            if self.driver.find_elements_by_xpath('//*[@id="pdf"]/div/div[2]/div[2]/div[1]'):
                break

            if self.driver.find_elements_by_xpath('//*[@id="conteudo"]/span/table[1]/tbody/tr[4]/td/h2'):
                break

        # "btns = document.getElementsByClassName("rodape-confirma'); if(btns.length > 1 && btns[1].textContent == ' Prolongar sessão '){btns[1].click();}'
        # self.driver.execute_script("btns = document.getElementsByClassName('rodape-confirma'); if(btns.length > 1 && btns[1].textContent == ' Prolongar sessão '){btns[1].click();}")

        self.driver.switch_to.default_content()
        btn = self.driver.find_element_by_xpath('//*[@id="modalUserIdleTimeout"]/div/div/div[3]/a[1]/div')
        if btn and btn.is_displayed():
            self.driver.execute_script("arguments[0].click();", btn)

        modal = self.driver.find_element_by_class_name('modal-backdrop')
        if modal and modal.is_displayed():
            self.driver.execute_script("arguments[0].remove();", modal)

        iframe_processo = self.driver.find_element_by_xpath('//*[@id="corpo"]/app-iframe/section/iframe')
        self.driver.switch_to_frame(iframe_processo)

        if self.grau == 1:
            if not self.driver.find_elements_by_xpath('//*[@id="pdf"]/div/div[2]/div[2]/div[1]/div/span/b'):

                inicio = time.time()
                links = self.driver.find_elements_by_xpath('//*[@id="porNumero"]/div[3]/div/p-table/div/div/table/tbody/tr/td[1]/a')
                while len(links) < 1:
                    if time.time() - inicio > 45:
                        raise MildException("Timeout ao buscar processo", self.uf, self.plataforma, self.prc_id)

                    links = self.driver.find_elements_by_xpath('//*[@id="porNumero"]/div[3]/div/p-table/div/div/table/tbody/tr/td[1]/a')

                for link in links:
                    numero_proc = ajusta_numero(link.text)
                    if numero_proc.find(numero_busca):
                        try:
                            link.click()
                        except:
                            self.driver.execute_script("btns = document.getElementsByClassName('rodape-confirma'); if(btns.length > 1 && btns[1].textContent == ' Prolongar sessão '){btns[1].click();}")
                            link.click()
                        break

        else:
            if not self.driver.find_elements_by_xpath('//*[@id="conteudo"]/span/table[1]/tbody/tr[4]/td/h2'):
                time.sleep(1)
                self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')

                inicio = time.time()
                links = self.driver.find_elements_by_xpath('//*[@id="porNumero"]/div[3]/div/p-table/div/div/table/tbody/tr/td[1]/a')
                while len(links) < 1:
                    if time.time() - inicio > 45:
                        raise MildException("Timeout ao buscar processo", self.uf, self.plataforma, self.prc_id)
                    links = self.driver.find_elements_by_xpath('//*[@id="porNumero"]/div[3]/div/p-table/div/div/table/tbody/tr/td[1]/a')

                for link in links:
                    rec_url = link.find_element_by_xpath('span').text.strip()
                    rec_url = rec_url.replace('(','').replace(')','').replace('.','').replace('-','').strip()
                    codigo = codigo.replace('(','').replace(')','').replace('.','').replace('-','').strip()
                    print('rec_url', rec_url, codigo)
                    if rec_url == codigo:
                        # self.driver.execute_script("arguments[0].click();", link)
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


        cancelado = self.driver.find_element_by_xpath('//*[@id="pdf"]/div/div[2]/div[2]/div[3]/div[2]/label')
        if cancelado:
            if cancelado.text.find('PROCESSO CANCELADO') > -1:
                return True

        movimentos = self.driver.find_elements_by_tag_name('app-movimento')
        ultima_mov = movimentos[0]

        tipo = ultima_mov.find_element_by_xpath('div[1]').text
        tipo = tipo.replace('Tipo do Movimento:','')
        # acp_cadastro = ultima_mov.find_element_by_xpath('div[2]/div[1]/label[2]').text
        datas = ultima_mov.find_elements_by_xpath('div[2]/div/label[2]')

        for d in datas:
            acp_cadastro = d.text
            # acp_cadastro = dia.find_element_by_xpath('td[2]').text
            if len(acp_cadastro) < 12:
                try:
                    acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y')
                except:
                    continue
            else:
                try:
                    acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y %H:%M')
                except:
                    continue

            break

        return Acompanhamento.compara_mov(base, prc_id, tipo.strip(), acp_cadastro, self.plataforma, self.grau, campo = 'acp_tipo',
                                          rec_id=self.rec_id)

    # CAPTURA ACOMPANHAMENTOS DO PROCESSO
    def acompanhamentos(self, proc_data, completo, base):
        '''
        :param datetime Última movimentação registrada na base
        :param bool Realiza a captura completa das movimentações
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        prc_id = proc_data['prc_id']
        rec_id = proc_data['rec_id'] if 'rec_id' in proc_data else None
        movs = []
        self.movs = []

        # CARREGA TODAS AS MOVIMENTAÇÔES
        # self.driver.find_element_by_xpath('//*[@id="pdf"]/div/div[1]/div[2]/button[2]').click()
        self.driver.execute_script("teste = document.getElementsByClassName('botoes-superiores'); teste2 = teste[0].getElementsByClassName('botao-pesquisar'); teste2[1].click();")

        if self.grau == 1:
            self.insert_recursos(base, proc_data)

        lista = Acompanhamento.lista_movs(base, prc_id, self.plataforma, acp_grau=self.grau, rec_id=rec_id)
        print(lista)
        self.wait_load()

        capturar = False
        inicio = time.time()
        while True:
            if time.time() - inicio > 120:
                raise MildException("Timeout ao capturar movimentações", self.uf, self.plataforma, self.prc_id)

            inicio_mov = time.time()
            movimentos = []
            while len(movimentos) < 1:
                if time.time() - inicio_mov > 30:
                    raise MildException("Timeout ao carregar lista de movimentações", self.uf, self.plataforma, self.prc_id)

                movimentos = self.driver.find_elements_by_xpath('//*[@id="movimentacaoProcessoC"]/div[1]/div/app-movimento')

            i = 0
            for movimento in movimentos:
                i += 1
                acp_cadastro = None
                acp_esp = ''

                tipo = movimento.find_element_by_xpath('div[1]').text
                acp_tipo = tipo.replace('Tipo do Movimento:', '').strip()
                acp_tipo = acp_tipo.replace('  ',' ')
                datas = movimento.find_elements_by_xpath('div/div/label')
                for d in datas:
                    if acp_cadastro is None:
                        if len(d.text) < 12:
                            try:
                                acp_cadastro = datetime.strptime(d.text, '%d/%m/%Y')
                                continue
                            except:
                                pass
                        else:
                            try:
                                acp_cadastro = datetime.strptime(d.text, '%d/%m/%Y %H:%M')
                                continue
                            except:
                                pass

                    if acp_cadastro is not None:
                        acp_esp += ' '+d.text.replace('Descrição:','')

                if acp_cadastro is None:
                    raise MildException("Data não localizada", self.uf, self.plataforma, self.prc_id)

                acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp.strip(), 'acp_tipo': acp_tipo}

                capturar = True
                for l in lista:
                    acp_tipo_base = l['acp_tipo'].replace('  ', ' ')
                    if acp_cadastro == l['acp_cadastro'] and acp_tipo_base.upper().strip() == acp_tipo.upper().strip():
                        capturar = False
                        break

                self.movs.append({**acp, 'novo': capturar})
                if capturar:
                    movs.append(acp)

                    if not completo and i >= 10:
                        break


            if not self.driver.find_element_by_xpath('//*[@id="movimentacaoProcessoC"]/div[1]/div[12]/p-paginator/div/button[3]') or (not completo and not capturar):
                break
            else:
                arg  = self.driver.find_element_by_id('movimentacaoProcessoC')
                arg = arg.find_element_by_class_name('p-paginator-next')
                self.driver.execute_script("arguments[0].click();", arg)
                # self.driver.execute_script("btn = document.getElementsByClassName('p-paginator-next'); btn[0].click();", arg)
            # try:
            #     self.driver.execute_script("btn = document.getElementsByClassName('p-paginator-next'); btn[0].click();")
            #     self.driver.find_element_by_xpath('//*[@id="movimentacaoProcessoC"]/div[1]/div[12]/p-paginator/div/button[3]').click()
            # except:
            #     break

        print(self.movs)
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

        link = False
        labels = self.driver.find_elements_by_class_name('form-dados-estaticos')
        for label in labels:
            if label.text == 'Listar todos os personagens':
                self.driver.execute_script("arguments[0].click();", label)
                link = True
                break

        # link = self.driver.find_element_by_xpath('//*[@id="pdf"]/div/div[2]/div[2]/div[7]/div[6]/label[2]/span')
        if link:
        #     self.driver.execute_script("arguments[0].click();", link)
            # link.click()

            time.sleep(1)
            partes = self.driver.find_elements_by_xpath('//*[@id="lista-personagens"]/div/div/div[2]/div/div/p-table/div/div/table/tbody/tr')
            i = 0
            for parte in partes:
                i += 1
                prr_nome = self.driver.find_element_by_xpath('//*[@id="lista-personagens"]/div/div/div[2]/div/div/p-table/div/div/table/tbody/tr['+str(i)+']/td[2]')
                if not prr_nome:
                    continue

                # tipo = parte.find_element_by_xpath('td[1]').text
                tipo = self.driver.find_element_by_xpath('//*[@id="lista-personagens"]/div/div/div[2]/div/div/p-table/div/div/table/tbody/tr['+str(i)+']/td[1]').text

                if tipo in ('Advogado', ''):
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
                    raise MildException("polo vazio "+tipo, self.uf, self.plataforma, self.prc_id)

                prts[polo].append({'prt_nome': prr_nome.text.strip(), 'prt_cpf_cnpj': 'Não Informado'})

        else:
            i = 2
            partes = self.driver.find_elements_by_xpath('//*[@id="pdf"]/div/div[2]/div[2]/div[7]/div/label[1]')
            for parte in partes:
                i += 1
                tipo = parte.text
                polo = ''
                if find_string(tipo, self.titulo_partes['ativo']):
                    polo = 'ativo'
                if find_string(tipo, self.titulo_partes['passivo']):
                    polo = 'passivo'
                if find_string(tipo, self.titulo_partes['terceiro']):
                    polo = 'terceiro'

                if polo == '':
                    continue

                prr_nome = self.driver.find_element_by_xpath('//*[@id="pdf"]/div/div[2]/div[2]/div[7]/div['+str(i)+']/label[2]').text
                prts[polo].append({'prt_nome': prr_nome, 'prt_cpf_cnpj': 'Não Informado'})

        return prts


    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []

        partes = self.driver.find_elements_by_xpath('//*[@id="lista-personagens"]/div/div/div[2]/div/div/p-table/div/div/table/tbody/tr')
        # link = self.driver.find_element_by_xpath('//*[@id="pdf"]/div/div[2]/div[2]/div[7]/div[6]/label[2]/span')
        if len(partes) == 0:
            return resps

        if not partes[0].is_displayed():
            return resps

        polo = ''
        i = 0
        for parte in partes:
            i += 1
            advogados = self.driver.find_element_by_xpath('//*[@id="lista-personagens"]/div/div/div[2]/div/div/p-table/div/div/table/tbody/tr[' + str(i) + ']/td[2]')
            if not advogados:
                continue

            tipo = self.driver.find_element_by_xpath('//*[@id="lista-personagens"]/div/div/div[2]/div/div/p-table/div/div/table/tbody/tr[' + str(i) + ']/td[1]').text

            if tipo != 'Advogado':
                if find_string(tipo, self.titulo_partes['ignorar']):
                    continue

                polo = ''
                if find_string(tipo, self.titulo_partes['ativo']):
                    polo = 'Polo Ativo'
                    continue
                if find_string(tipo, self.titulo_partes['passivo']):
                    polo = 'Polo Passivo'
                    continue


                # if polo == '':
                #     raise MildException("polo vazio " + tipo, self.uf, self.plataforma, self.prc_id)

            if polo == '':
                raise MildException("polo vazio "+tipo, self.uf, self.plataforma, self.prc_id)

            advogados = advogados.text
            f = advogados.find(')')
            prr_oab = advogados[1:f].strip()
            prr_nome = advogados[f + 1:].strip()
            resps.append({'prr_nome': prr_nome, 'prr_oab': prr_oab, 'prr_cargo': 'Advogado', 'prr_parte': polo})

        self.driver.find_element_by_xpath('//*[@id="lista-personagens"]/div/div/div[3]/a[2]/div').location_once_scrolled_into_view
        self.driver.find_element_by_xpath('//*[@id="lista-personagens"]/div/div/div[3]/a[2]/div').click()
        return resps

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
        xpath_titulo = '//*[@id="pdf"]/div/div[2]/div[2]/div[1]/div'
        n = self.driver.find_element_by_xpath(xpath_titulo)
        if not n:
            xpath_titulo = '//*[@id="conteudo"]/span/table[1]/tbody/tr[4]/td/h2'

        prc_numero2 = ''
        while prc_numero2 == '':
            prc_numero2 = self.driver.find_element_by_xpath(xpath_titulo).text

        prc['prc_numero2'] = localiza_cnj(prc_numero2)
        campos = {'Classe': 'prc_classe', 'Assunto': 'prc_assunto', 'Comarca': 'prc_comarca2','Serventia': 'prc_serventia', }

        divs = self.driver.find_element_by_xpath('//*[@id="pdf"]/div/div[2]/div[2]/div[6]')
        linhas = divs.find_elements_by_class_name('control-label')
        conts = divs.find_elements_by_class_name('form-dados-estaticos')
        i = -1
        for linha in linhas:
            i += 1

            titulo = linha.text
            for cmp in campos:
                if titulo.upper() == cmp.upper():
                    prc[campos[cmp]] = conts[i].text.strip()
                    break

        if 'prc_comarca2' in prc:
            prc['prc_comarca2'] = localiza_comarca(prc['prc_comarca2'], self.uf)

        return prc

    # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS
    def download(self, prc_id, arquivos_base, pendentes, target_dir):
        return []

    # FECHA A JANELA DO PROCESSO ABERTO ATUALMENTE
    def fecha_processo(self):
        self.driver.switch_to.window(self.driver.window_handles[-1])

   # AGUARDA ATÉ QUE A ANIMAÇÃO DE LOADING ESTEJA OCULTA
    def wait_load(self, tempo=30):
        if self.driver.find_element_by_id('loadingbox'):
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

        app_loading = self.driver.find_element_by_xpath('/html/body/app-root/app-detalhes-processo/app-loading/div/div/span')
        if app_loading:
            inicio = time.time()
            while self.driver.find_element_by_xpath('/html/body/app-root/app-detalhes-processo/app-loading/div/div/span'):
                time.sleep(0.2)
                if time.time() - inicio > tempo:
                    raise MildException("Loading Timeout", self.uf, self.plataforma, self.prc_id, False)

        return True