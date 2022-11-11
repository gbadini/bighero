from Controllers.Tribunais.Pje._pje import *

# CLASSE DA VARREDURA DO PJE DO DF. HERDA OS METODOS DA CLASSE PJE
class DF(Pje):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.tjdft.jus.br/pje/login.seam"
        # self.pagina_busca = "https://pje.tjdft.jus.br/pje/Processo/CadastroPeticaoAvulsa/peticaoavulsa.seam"
        self.pagina_busca = "https://pje.tjdft.jus.br/pje/Processo/ConsultaProcesso/listView.seam"

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        ordem = numero_busca[0:7]
        digito1 = numero_busca[7:9]
        ano = numero_busca[9:13]
        justica = numero_busca[13:14]
        tribunal = numero_busca[14:16]
        digito2 = numero_busca[16:]

        aguarda_alerta(self.driver, tempo=0, aceitar=False)

        if not self.driver.find_element_by_xpath('//*[@id="fPP:numProcessoDiv"]/div/div/div[2]/input[1]'):
            raise CriticalException("Erro ao buscar processo (Unhandled Exception)", self.uf, self.plataforma, self.prc_id)

        if not self.driver.find_element_by_xpath('//*[@id="fPP:numProcessoDiv"]/div/div/div[2]/input[1]').is_displayed():
            raise MildException("Erro ao buscar processo (Campo Oculto)", self.uf, self.plataforma, self.prc_id, False)

        for i in range(1, 6):
            try:
                self.driver.find_element_by_xpath('//*[@id="fPP:numProcessoDiv"]/div/div/div[2]/input['+str(i)+']').clear()
            except InvalidElementStateException:
                pass

        self.driver.find_element_by_xpath('//*[@id="fPP:numProcessoDiv"]/div/div/div[2]/input[1]').send_keys(ordem)
        self.driver.find_element_by_xpath('//*[@id="fPP:numProcessoDiv"]/div/div/div[2]/input[2]').send_keys(digito1)
        self.driver.find_element_by_xpath('//*[@id="fPP:numProcessoDiv"]/div/div/div[2]/input[3]').send_keys(ano)
        try:
            self.driver.find_element_by_xpath('//*[@id="fPP:numProcessoDiv"]/div/div/div[2]/input[4]').send_keys(justica)
        except InvalidElementStateException:
            pass
        self.driver.find_element_by_xpath('//*[@id="fPP:numProcessoDiv"]/div/div/div[2]/input[5]').send_keys(tribunal)
        self.driver.find_element_by_xpath('//*[@id="fPP:numProcessoDiv"]/div/div/div[2]/input[6]').send_keys(digito2)

        self.driver.find_element_by_xpath('//*[@id="fPP:numProcessoDiv"]/div/div/div[2]/input[6]').send_keys(Keys.ENTER)
        self.wait()
        self.wait(30, 'modalStatusContainer')

        try_click(self.driver, '//*[@id="popupAlertaCertificadoProximoDeExpirarContentDiv"]/div/form')
        if not aguarda_presenca_elemento(self.driver, 'fPP:processosTable:tb', tipo='ID'):
            raise MildException("Erro ao buscar processo (tabela não localizada)", self.uf, self.plataforma, self.prc_id, False)

        # CONFERE SE JA CARREGOU A LISTAGEM
        trs = self.driver.find_elements_by_xpath('//*[@id="fPP:processosTable:tb"]/tr')
        if len(trs) == 0 and not check_text(self.driver, '//*[@id="fPP:processosGridPanel_body"]/dl', 'NÃO FOI ENCONTRADO'):
            time.sleep(1)

        if check_text(self.driver, '//*[@id="fPP:processosGridPanel_body"]/dl', 'NÃO FOI ENCONTRADO'):
            return False

        inicio = time.time()
        while True:
            footer = self.driver.find_element_by_xpath('//*[@id="fPP:processosTable"]/tfoot/tr/td/div/div[2]/span')

            if footer.text == '0 resultados encontrados' or footer.text == '0 resultados encontrados.' or footer.text == 'resultados encontrados.':
                return False

            if footer.text != '0 resultados encontrados' and footer.text != 'resultados encontrados.' and footer.text != '0 resultados encontrados.':
                return True

            if time.time() - inicio > 2:
                trs = self.driver.find_elements_by_xpath('//*[@id="fPP:processosTable:tb"]/tr')
                if len(trs) == 0:
                    raise MildException("Erro ao buscar processo", self.uf, self.plataforma, self.prc_id, False)

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        self.confere_cnj(numero_busca)


        # CAPTURA OS ARQUIVOS SALVOS NA BASE
        arquivos_base = ProcessoArquivo.select(self.active_conn, self.proc_data['prc_id'], self.plataforma, pra_grau=None)
        # VERIFICA QUAIS ARQUIVOS ESTÃO COM O DOWNLOAD PENDENTE
        pend = False
        for arb in arquivos_base:
            if arb['pra_erro']:
                if arb['pra_legado']:
                    break
                pend = True
                break
                
        if self.completo or self.proc_data['prc_data_pje'] is None or pend:
            self.abre_processo()

        # achei = False
        # if check_text(self.driver, '//*[@id="fPP:processosPeticaoGridPanel_body"]/dl', 'sigilo'):
        #     achei = True
        #
        # exc = self.driver.find_element_by_class_name('fa-exclamation-circle')
        # if exc:
        #     achei = True
        #
        # if achei:
        #     if not self.driver.find_element_by_xpath('//*[@id="fPP:processosTable:tb"]/tr/td[1]/a[2]'):
        #         return True

        return False

    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''

        # CONFERE SE O PROCESSO ESTÁ HABILITADO
        if not try_click(self.driver, '//*[@id="fPP:processosTable:tb"]/tr[1]/td[1]/a[1]'):
            raise MildException("Botão de abrir não localizado", self.uf, self.plataforma, self.prc_id, False)

        inicio = time.time()
        while True:
            wh = self.driver.window_handles
            # SE O PROCESSO ESTÁ HABILITADO, CHAMA O MÉTODO PADRÃO
            if len(wh) == 2:
                self.alterna_janela()
                if check_text(self.driver, '//*[@id="pageBody"]/div/div[2]/pre/dl', 'Sem permissão para acessar a página'):
                    self.fecha_processo()
                    self.abre_aba_processo()
                    self.wait(10)
                    if check_text(self.driver, '//*[@id="pageBody"]/div/div[2]/pre/dl',
                                  'Sem permissão para acessar a página'):
                        raise MildException("Erro de permissão", self.uf, self.plataforma, self.prc_id)
                return super().ultima_movimentacao(ultima_data, prc_id, base)

            # SE NÃO ESTÁ HABILITADO, CONTINUA NO METODO CUSTOMIZADO
            if aguarda_alerta(self.driver, tempo=0.1, aceitar=False, rejeitar=True):
                break

            # CONFERE SE O PAINEL AVISANDO SOBRE O LIMITE DE CONSULTAS ESTÁ SENDO EXIBIDO
            if (time.time() - inicio) >= 10:
                panel = self.driver.find_element_by_xpath('//*[@id="panelAlertaContentTable"]/tbody/tr[2]/td')
                if panel and panel.is_displayed():
                    if panel.text.upper().find('LIMITE DIÁRIO DE CONSULTAS') > -1:
                        raise FatalException('Limite diário excedido. Utilizar outro certificado', self.uf, self.plataforma, self.prc_id)
                else:
                    raise MildException("Erro ao buscar processo (Detecção de Alert)", self.uf, self.plataforma, self.prc_id, False)

        lista = Acompanhamento.lista_movs(base, prc_id, self.plataforma, rec_id=self.rec_id, acp_grau=self.grau, order_by=True)
        lista.reverse()
        for i,l in enumerate(lista):
            r = re.search(r"(\d+)", l['acp_tipo'])
            if r:
                if r.group(0) == l['acp_tipo'] and len(l['acp_tipo']) >= 8:
                    continue

            ultima_mov = l
            break

        ultima_esp = self.driver.find_element_by_xpath('//*[@id="fPP:processosTable:tb"]/tr/td[8]').text
        ultima_esp = self.prepara_ultima_mov(ultima_esp)
        for i,l in enumerate(lista):
            if self.prepara_ultima_mov(l['acp_esp']) == ultima_esp:
                if l['acp_cadastro'] == ultima_mov['acp_cadastro']:
                    # print(self.prepara_ultima_mov(l['acp_esp']), ultima_esp)
                    return True

            if i == 10:
                break

        # ultima_esp = self.driver.find_element_by_xpath('//*[@id="fPP:processosTable:tb"]/tr/td[8]').text
        # print(ultima_mov['acp_esp'], ultima_esp)
        # if ultima_mov['acp_esp'].upper().strip() == ultima_esp.upper().strip():
        #     return True
        if not self.nao_varrer:
            self.abre_processo()

        return False

    def prepara_ultima_mov(self, texto):
        texto = texto.upper()
        return texto.strip()

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        aguarda_presenca_elemento(self.driver,'//*[@id="fPP:processosTable:tb"]/tr/td[1]')
        el = self.driver.find_element_by_xpath('//*[@id="fPP:processosTable:tb"]/tr/td[1]')
        if el:
            numero_site = ajusta_numero(el.text)
            if numero_busca == numero_site:
                return True

        raise MildException("Número CNJ Diferente", self.uf, self.plataforma, self.prc_id)