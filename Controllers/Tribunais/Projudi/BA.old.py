from Controllers.Tribunais.Projudi._projudi_v2 import *
from Config.helpers import *


# CLASSE DA VARREDURA DO PROJUDI DA BA. HERDA OS METODOS DA CLASSE PROJUDI
class BA(ProjudiV2):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://projudi.tjba.jus.br/projudi/PaginaPrincipal.jsp"
        self.pagina_busca = "https://projudi.tjba.jus.br/projudi/buscas/ProcessosQualquerAdvogado"
        self.pagina_processo = "https://projudi.tjba.jus.br/projudi/listagens/DadosProcesso?numeroProcesso="
        self.reiniciar_navegador = False
        self.arquiva_sentenca = False
        self.wait_loading = False
        self.tabela_movs = '//*[@id="Arquivos"]/table/tbody/tr/td/table/tbody/tr'
        self.posicao_elementos = {'tipo': 1, 'esp': 2, 'data': 3, 'usr': 4}
        self.formato_data = '%d/%m/%y'

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''

        if not aguarda_presenca_elemento(self.driver, '//*[@id="formLogin"]/table/tbody/tr[6]/td[2]/a'):
            return False

        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="formLogin"]/table/tbody/tr[6]/td[2]/a')))
        except TimeoutException:
            pass

        self.driver.find_element_by_id("login").send_keys(usuario)
        self.driver.find_element_by_id("senha").send_keys(senha)
        while True:
            try:
                self.driver.execute_script("javascript:submeter('acesso');")
                break
            except:
                pass

        time.sleep(10)
        while self.driver.find_element_by_xpath('//*[@id="formLogin"]/table/tbody/tr[6]/td[2]/a'):
            time.sleep(2)
            if not self.driver.find_element_by_xpath('//*[@id="formLogin"]/table/tbody/tr[6]/td[2]/a'):
                time.sleep(2)
                self.driver.execute_script("window.stop();")

        if not aguarda_presenca_elemento(self.driver, 'BarraMenu', tipo='ID'):
            return False

        return True

    # CONFERE SE O CÓDIGO É VALIDO
    def check_codigo(self, codigo):
        '''
        :param str codigo: codigo _GET de acesso
        '''
        if codigo is None:
            return False

        if codigo.strip() == '':
            return False

        if codigo.find('/') > -1 or codigo.find('-') > -1:
            return False

        return True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        if not aguarda_presenca_elemento(self.driver, 'numeroProcesso', tipo='ID'):
            raise CriticalException("Campo de busca não localizado", self.uf, self.plataforma, self.prc_id, False)

        inicio = time.time()
        while True:
            if time.time() - inicio > 10:
                raise MildException("Timeout Campo Busca", self.uf, self.plataforma, self.prc_id, False)
            try:
                self.driver.find_element_by_id('numeroProcesso').clear()
                self.driver.find_element_by_id('numeroProcesso').send_keys(numero_busca)
                self.driver.find_element_by_id("numeroProcesso").send_keys(Keys.ENTER)
                break
            except:
                time.sleep(1)
                pass

        inicio = time.time()
        while True:
            if time.time() - inicio > 10:
                print('Timeout Busca')
                raise CriticalException("Timeout Busca", self.uf, self.plataforma, self.prc_id, False)

            if self.driver.find_element_by_class_name('erro'):
                if self.driver.find_element_by_class_name('erro').text.find('Verifique os seguintes erros') > -1:
                    return False

            if self.driver.find_element_by_xpath('/html/body/div[1]/form[2]/table/tbody/tr[3]/th[2]/a'):
                break

            if self.driver.find_element_by_xpath('/html/body/strong[2]/p/a'):
                aguarda_presenca_elemento(self.driver,'/html/body/div[1]/form[2]/table/tbody/tr[4]/td[2]/a', tempo=2)
                break

            if self.driver.find_element_by_xpath('//*[@id="Partes"]/table/tbody/tr[1]/td'):
                break

        cnj = self.driver.find_element_by_xpath('/html/body/div[1]/form[2]/table/tbody/tr[4]/td[2]/a')
        if not cnj:
            return False

        return True

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        # a = self.driver.find_element_by_xpath('/html/body/div[1]/form[2]/table/tbody/tr[4]/td[2]/a')
        # if a:
        #     cnj = ajusta_numero(a.text)
        #     if cnj != numero_busca:
        #         raise MildException("Número CNJ Diferente na busca", self.uf, self.plataforma, self.prc_id)
        #     a.click()
        #     aguarda_alerta(self.driver, tempo=2)

        inicio = time.time()
        while True:
            if time.time() - inicio > 40:
                self.driver.execute_script("window.stop();")
                raise MildException("Timeout Abrir Processo", self.uf, self.plataforma, self.prc_id, False)

            if try_click(self.driver, '/html/body/div[1]/form[2]/table/tbody/tr[4]/td[2]/a'):
                aguarda_alerta(self.driver, tempo=2)

            try:
                aguarda_alerta(self.driver, tempo=0.1)

                if self.driver.find_element_by_xpath('//*[@id="Partes"]/table/tbody/tr[1]/td'):
                    break

                if self.driver.find_element_by_xpath('/html/body/strong[2]/p/a'):
                    el = self.driver.find_element_by_xpath('/html/body/strong[1]/p')
                    if el:
                        if el.text.find('Segredo de Justiça') > -1:
                            return True
            except:
                tb = traceback.format_exc()
                print(tb)
                pass

            aguarda_alerta(self.driver, tempo=0.1)
            erro = self.driver.find_element_by_xpath('/html/body/center/strong')
            if erro:
                if erro.text.find('ERRO') > -1:
                    raise MildException("Erro java ao abrir processo", self.uf, self.plataforma, self.prc_id, False)

        aguarda_alerta(self.driver, tempo=0.2)

        self.confere_cnj(numero_busca)
        return False

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        cnj = self.driver.find_element_by_xpath('//*[@id="Partes"]/table/tbody/tr[1]/td/b/font/a')

        cnj_limpo = ajusta_numero(cnj.text)
        if cnj_limpo != numero_busca:
            cnj = self.driver.find_element_by_xpath('//*[@id="Partes"]/table/tbody/tr[1]/td/b/font[2]')
            if cnj:
                cnj_limpo = cnj.text.replace('Nº Antigo:','')
                cnj_limpo = ajusta_numero(cnj_limpo.strip())
                if cnj_limpo == numero_busca:
                    return True

            raise MildException("Número CNJ Diferente", self.uf, self.plataforma, self.prc_id)

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        if not aguarda_presenca_elemento(self.driver,'//*[@id="Arquivos"]/table/tbody/tr[2]/td/table/tbody/tr/td[3]'):
            raise MildException("Última mov. não localizada", self.uf, self.plataforma, self.prc_id)

        data_ultima_mov = self.driver.find_element_by_xpath('//*[@id="Arquivos"]/table/tbody/tr[2]/td/table/tbody/tr/td[3]').text
        data_ultima_mov = strip_html_tags(data_ultima_mov)
        data_ultima_mov = data_ultima_mov[:6]+'20'+data_ultima_mov[6:]+' 00:00'
        data_cad = datetime.strptime(data_ultima_mov, '%d/%m/%Y %H:%M')

        acp_tipo = self.driver.find_element_by_xpath('//*[@id="Arquivos"]/table/tbody/tr[2]/td/table/tbody/tr/td[1]').get_attribute('innerHTML')
        acp_tipo = acp_tipo.replace('\r','').replace('\n','').replace('&nbsp;','')

        acp_tipo = strip_html_tags(acp_tipo)
        acp_tipo = acp_tipo.strip()

        return Acompanhamento.compara_mov(base, prc_id, acp_tipo, data_cad, self.plataforma, self.grau, campo='acp_tipo')

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
        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(EC.presence_of_all_elements_located((By.XPATH, self.tabela_movs)))
        except TimeoutException:
            raise MildException("Erro ao carregar tabela de movs.", self.uf, self.plataforma, self.prc_id)

        movs = []
        self.movs = []

        movimentos = self.driver.find_elements_by_xpath(self.tabela_movs)
        capturar = True
        fim = False
        i = 0
        if len(movimentos) == 0:
            raise MildException("Erro ao capturar tabela de movs.", self.uf, self.plataforma, self.prc_id)

        movimentos.pop(0)

        lista = Acompanhamento.lista_movs(base, prc_id, self.plataforma)
        for mov in movimentos:
            acps_cadastro = mov.find_elements_by_xpath('td['+str(self.posicao_elementos['data'])+']')
            if len(acps_cadastro) == 0:
                continue
            acp_tipo = mov.find_element_by_xpath('td[' + str(self.posicao_elementos['tipo']) + ']').text
            acp_tipo = strip_html_tags(acp_tipo)
            acp_cadastro = datetime.strptime(acps_cadastro[0].text, self.formato_data)

            if completo:
                capturar = True

            i += 1
            for l in lista:
                tipo_base = strip_html_tags(l['acp_tipo'])
                if acp_cadastro == l['acp_cadastro'] and tipo_base == acp_tipo:
                    capturar = False
                    if not completo and i >= 10:
                        fim = True
                        break

            if fim:
                break

            acp_esp = mov.find_element_by_xpath('td[' + str(self.posicao_elementos['esp']) + ']').text
            acp_usuario = mov.find_element_by_xpath('td[' + str(self.posicao_elementos['usr']) + ']').text
            acp_esp = strip_html_tags(acp_esp)
            acp_usuario = strip_html_tags(acp_usuario)

            acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp.strip(), 'acp_tipo': acp_tipo.strip(), 'acp_usuario': acp_usuario.strip()}
            if capturar:
                movs.append(acp)

            self.movs.append({**acp, 'novo': capturar})

        return movs

    # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS
    def download(self, prc_id, arquivos_base, pendentes, pasta_intermediaria):
        return []