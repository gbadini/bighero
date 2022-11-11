from Controllers.Tribunais.Fisico._fisico import *
import urllib.parse as urlparse
from urllib.parse import parse_qs

# CLASSE DA VARREDURA DO FISICO DE PE. HERDA OS METODOS DA CLASSE FISICO
class PE(Fisico):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "chrome://version/"
        self.pagina_busca = "https://srv01.tjpe.jus.br/consultaprocessualunificada/processo/"
        # self.pagina_processo = "https://srv01.tjpe.jus.br/consultaprocessualunificada/processo/"
        self.formato_data = '%d/%m/%Y %H:%M'
        # self.reiniciar_navegador = False
        self.titulo_partes = get_tipo_partes(grau=2)
        self.titulo_partes['ativo'] += ('PROCURADORIA DE JUSTIÇA',)
        self.titulo_partes['passivo'] += ('REPRESENTANTE',)
        self.pje2g = False
        # self.pagina_processo = "https://www4.tjmg.jus.br/juridico/sf/proc_resultado.jsp?tipoPesquisa=1&nomePessoa=&tipoPessoa=X&naturezaProcesso=0&situacaoParte=X&codigoOAB=&tipoOAB=N&ufOAB=MG&numero=1&select=1&tipoConsulta=1&natureza=0&ativoBaixado=X&https://www4.tjmg.jus.br/juridico/sf/proc_resultado.jsp?tipoPesquisa=1&nomePessoa=&tipoPessoa=X&naturezaProcesso=0&situacaoParte=X&codigoOAB=&tipoOAB=N&ufOAB=MG&numero=1&select=1&tipoConsulta=1&natureza=0&ativoBaixado=X&https://www4.tjmg.jus.br/juridico/sf/proc_resultado.jsp?tipoPesquisa=1&nomePessoa=&tipoPessoa=X&naturezaProcesso=0&situacaoParte=X&codigoOAB=&tipoOAB=N&ufOAB=MG&numero=1&select=1&tipoConsulta=1&natureza=0&ativoBaixado=X&listaProcessos="

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        self.wait()
        aguarda_presenca_elemento(self.driver, '/html/body/div/div[2]/ui-view/section[2]/ng-include/div/div/div/div/form/div[1]/div/div[1]/div/div[2]/div[2]/div/input', aguarda_visibilidade=True)

        try:
            self.driver.find_element_by_xpath(
                '/html/body/div/div[2]/ui-view/section[2]/ng-include/div/div/div/div/form/div[1]/div/div[1]/div/div[2]/div[2]/div/input').send_keys(numero_busca)
        except:
            raise MildException("Erro na Busca", self.uf, self.plataforma, self.prc_id)

        # Verifica se tem captcha
        # Se tiver captcha aguarda até digitação do captcha
        # Senão clica direto no botão Consultar

        captcha = self.driver.find_element_by_id('captcha')
        if not captcha:
            self.process_main_child = foca_janela(self.process_main_child)
            try:
                self.driver.find_element_by_class_name('button-consultar').click()
            except:
                time.sleep(2)
                self.driver.find_element_by_class_name('button-consultar').click()

            self.wait()
        else:
            self.captcha(numero_busca)

        self.wait()
        #CONFERIR SE O CAMPO DE BUSCA ESTÁ VAZIO E NÃO POSSUI MENSAGEM DE ERRO, DAR UM RAISE
        campo = self.driver.find_element_by_xpath('/html/body/div/div[2]/ui-view/section[2]/ng-include/div/div/div/div/form/div[1]/div/div[1]/div/div[2]/div[2]/div/input')
        if campo.get_attribute('value') == '':
            raise MildException("Erro na Busca", self.uf, self.plataforma, self.prc_id)

        msg = self.driver.find_element_by_xpath('/html/body/div/div[2]/ui-view/section[2]/ng-include/div/div[1]')
        if msg:
            if msg.text.find('Não foram encontradas informações') > -1:
                return False


        erro = self.driver.find_element_by_xpath('/html/body/div/div[2]/ui-view/section[2]/ng-include/div/div[1]/div/span/li')
        if erro:
            if erro.text.find('Valor indicado para a imagem') > -1:
                raise MildException("Erro na busca (captcha)", self.uf, self.plataforma, self.prc_id)

        uls = []
        while len(uls) == 0:
            uls = self.driver.find_elements_by_xpath("//ul[contains(@class, 'resultado-detalhe-item')]")

        # CONFERE SE É PROCESSO ELETRONICO
        for ul in uls:
            if ul.find_element_by_class_name('panel-heading').text.upper().find('1º GRAU - ELETRÔNICO') > -1:
                cnj = ul.find_element_by_xpath('uib-accordion/div/div/div[2]/div/h4').text
                cnj = localiza_cnj(cnj)
                cnj = ajusta_numero(cnj)
                if cnj == numero_busca:
                    return False

        # APAGAR DEPOIS DE PRONTO
        # if len(uls) > 1:
        #     raise FatalException("Nao foi dessa vez", self.uf, self.plataforma, self.prc_id)
        #
        # if uls[0].find_element_by_class_name('panel-heading').text.upper().find('1º GRAU - FÍSICO') == -1 and uls[0].find_element_by_class_name('panel-heading').text.upper().find('2º GRAU - FÍSICO') == -1:
        #     raise FatalException("Nao foi dessa vez tb", self.uf, self.plataforma, self.prc_id)

        return True

    def captcha(self, numero_busca):
        try:
            # Clica na caixa de digitação do captcha
            self.driver.find_element_by_id('captcha').click()
        except StaleElementReferenceException:
            time.sleep(3)
            self.driver.find_element_by_id('captcha').click()

        # inicio = time.time()
        while True:
            # Verifica se o tempo de resposta excedeu
            # tempoTotal = time.time() - inicio
            # if tempoTotal >= 60:
            #     print('\nTempo Limite de resposta atingido')
            #     raise MildException("Erro de tempo de Busca", self.uf, self.plataforma, self.prc_id)

            txt_capcha = self.driver.find_element_by_id('captcha').get_attribute('value')
            time.sleep(1)
            # Aguarda a digitação dos 5 caracteres
            if len(txt_capcha) != 5:
                continue

            campo_busca = self.driver.find_element_by_xpath(
                '/html/body/div/div[2]/ui-view/section[2]/ng-include/div/div/div/div/form/div[1]/div/div[1]/div/div[2]/div[2]/div/input').get_attribute('value')

            if campo_busca.strip() == '':
                self.driver.find_element_by_xpath(
                    '/html/body/div/div[2]/ui-view/section[2]/ng-include/div/div/div/div/form/div[1]/div/div[1]/div/div[2]/div[2]/div/input').send_keys(numero_busca)

            try:
                self.driver.find_element_by_xpath(
                    '/html/body/div/div[2]/ui-view/section[2]/ng-include/div/div/div/div/form/div[3]/div/button').click()
            except:
                raise MildException("Botão não localizado", self.uf, self.plataforma, self.prc_id, False)

            self.wait()
            # Se o captcha foi digitado errado e aparecer a mensagem de erro, continua no loop
            txt_falha = self.driver.find_element_by_xpath(
                '/html/body/div/div[2]/ui-view/section[2]/ng-include/div/div[1]/div/span/li')
            if txt_falha and txt_falha.text.find('Valor indicado para a imagem') > -1:
                continue

            break


    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        captcha = self.driver.find_element_by_id('captcha')
        if captcha:
            self.captcha(numero_busca)

        self.pje2g = False
        numero_site = ''
        uls = []
        while len(uls) == 0:
            uls = self.driver.find_elements_by_xpath("//ul[contains(@class, 'resultado-detalhe-item')]")

        self.uli = -1
        i = 0
        for ul in uls:
            if ul.find_element_by_class_name('panel-heading').text.upper().find('1º GRAU - FÍSICO') > -1:
                self.uli = i
                break

            i += 1

        if self.uli == -1:
            time.sleep(2)
            uls = self.driver.find_elements_by_xpath("//ul[contains(@class, 'resultado-detalhe-item')]")
            i = 0
            for ul in uls:
                if ul.find_element_by_class_name('panel-heading').text.upper().find('2º GRAU - FÍSICO') > -1:
                    self.uli = i
                i += 1

            if self.uli == -1:
                uls = self.driver.find_elements_by_xpath("//ul[contains(@class, 'resultado-detalhe-item')]")
                i = 0
                for ul in uls:
                    if ul.find_element_by_class_name('panel-heading').text.upper().find('2º GRAU - ELETRÔNICO') > -1:
                        self.uli = i
                        self.pje2g = True
                    i += 1

                if self.uli == -1:
                    raise MildException("painel fisico não localizado", self.uf, self.plataforma, self.prc_id)

        # aguarda_presenca_elemento(self.driver, "//ul[contains(@class, 'resultado-detalhe-item')]", aguarda_visibilidade=True)
        aguarda_presenca_elemento(self.driver, '/html/body/div/div[2]/ui-view/section[2]/ui-view/div/ul/uib-accordion/div/div/div[2]/div/h4', aguarda_visibilidade=True)

        el = self.driver.find_element_by_xpath('/html/body/div/div[2]/ui-view/section[2]/ui-view/div/ul/uib-accordion/div/div/div[2]/div/h4')
        if el:
            cnj = localiza_cnj(el.text)
            numero_site = ajusta_numero(cnj)
            if numero_busca == numero_site:
                return True

            el = self.driver.find_element_by_xpath('/html/body/div/div[2]/ui-view/section[2]/ui-view/div/ul[1]/uib-accordion/div/div/div[2]/div/div[1]/div')
            if el:
                cnj = localiza_cnj(el.text)
                if cnj:
                    numero_site = ajusta_numero(cnj)
                    if numero_busca == numero_site:
                        return True

        # print("Número CNJ Diferente - "+numero_site+" "+numero_busca)
        # time.sleep(999)
        raise MildException("Número CNJ Diferente - "+numero_site+" "+numero_busca, self.uf, self.plataforma, self.prc_id)

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        ul = self.driver.find_elements_by_xpath("//ul[contains(@class, 'resultado-detalhe-item')]")[self.uli]
        mov = ul.find_elements_by_class_name('result-movimentacoes')[0]
        data_ultima_mov = mov.find_element_by_xpath('label').text.strip()

        data_tj = datetime.strptime(data_ultima_mov, self.formato_data)
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

        movs = []
        self.movs = []
        i = 0
        capturar = True

        # CONFERE SE O PROCESSO FOI MIGRADO OU ESTÁ NO SEGUNDO GRAU
        uls = self.driver.find_elements_by_xpath("//ul[contains(@class, 'resultado-detalhe-item')]")
        recs = 0
        # IDENTIFICA SE É SOMENTE UM PROCESSO DE 2º GRAU
        if len(uls) == 1:
            if uls[0].find_element_by_class_name('panel-heading').text.upper().find('2º GRAU - ELETRÔNICO') > -1:
                cnj = uls[0].find_element_by_xpath('uib-accordion/div/div/div[2]/div/h4').text
                cnj = localiza_cnj(cnj)
                result = Recurso.select(base, rec_numero=cnj, rec_plt_id=2)
                if len(result) == 0:
                    time.sleep(1)
                    Recurso.insert(base, {'rec_prc_id': prc_id, 'rec_numero': cnj, 'rec_plt_id': 2})

                Processo.update_simples(base,prc_id,{'prc_data_fisico':datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'prc_fisico':False})
                raise MildException("Processo no Segundo Grau", self.uf, self.plataforma, self.prc_id)

        # SE TIVER MAIS DE UM PAINEL, IDENTIFICA SE É FISICO, ELETRONICO E GRAU
        if len(uls) > 1:
            achei1g = False
            for ul in uls:
                if ul.find_element_by_class_name('panel-heading').text.upper().find('1º GRAU - FÍSICO') > -1:
                    achei1g = True
                    break

            for ul in uls:
                cnj = ul.find_element_by_xpath('uib-accordion/div/div/div[2]/div/h4').text
                cnj = localiza_cnj(cnj)

                if ul.find_element_by_class_name('panel-heading').text.upper().find('2º GRAU - FÍSICO') > -1:
                    if achei1g:
                        result = Recurso.select(base, prc_id, rec_numero=cnj, rec_plt_id=4, rec_codigo=str(recs))
                        if len(result) == 0:
                            time.sleep(1)
                            Recurso.insert(base, {'rec_prc_id': prc_id, 'rec_numero': cnj, 'rec_plt_id':4, 'rec_codigo': recs})

                    recs += 1

                if ul.find_element_by_class_name('panel-heading').text.upper().find('1º GRAU - ELETRÔNICO') > -1:
                    if not Processo.processo_existe(base, cnj):
                        prc_pai = proc_data['prc_id'] if proc_data['prc_pai'] is None else proc_data['prc_pai']
                        np = [{'prc_numero': cnj, 'prc_estado': self.uf, 'prc_autor': proc_data['prc_autor'], 'prc_pai': prc_pai, 'prc_area': 1, 'prc_carteira': proc_data['prc_carteira']}, ]
                        time.sleep(1)
                        Processo.insert(base, np)
                        Processo.update_simples(base, prc_id, {'prc_migrado': True})

                if ul.find_element_by_class_name('panel-heading').text.upper().find('2º GRAU - ELETRÔNICO') > -1:
                    result = Recurso.select(base, rec_numero=cnj, rec_plt_id=2)
                    if len(result) == 0:
                        time.sleep(1)
                        Recurso.insert(base, {'rec_prc_id': prc_id, 'rec_numero': cnj, 'rec_plt_id': 2})

        ul = self.driver.find_elements_by_xpath("//ul[contains(@class, 'resultado-detalhe-item')]")[self.uli]
        # Clica em 'Exibir todas', caso exista mais de 5 processos


        # Movimentos antes clicar 'Exibir todas'
        movimentos = ul.find_elements_by_class_name('result-movimentacoes')
        len_antes = len(movimentos)
        links = ul.find_elements_by_partial_link_text('Exibir todas')
        if len(links) > 0:
            for link in links:
                link.click()

            if len(movimentos) < 5:
                inicio = time.time()
                while len_antes <= len(movimentos):
                    tempoTotal = time.time() - inicio
                    # Verifica se o tempo de resposta excedeu
                    if tempoTotal >= 30:
                        raise MildException("Erro ao carregar movimentações", self.uf, self.plataforma, self.prc_id)

                    movimentos = ul.find_elements_by_class_name('result-movimentacoes')
                    exbs = ul.find_elements_by_class_name('resultado-lista-div-mensagem')
                    ok = True
                    for exb in exbs:
                        if exb.text.find('Exibindo todas') == -1:
                            ok = False

                    if ok:
                        break

                    # len_antes = len(movimentos)

        movimentos = ul.find_elements_by_class_name('result-movimentacoes')
        for mov in movimentos:
            acp_cadastro = mov.find_element_by_xpath('label').text
            acp_cadastro = datetime.strptime(acp_cadastro, self.formato_data)

            i += 1
            if ultima_mov is not None:
                if acp_cadastro <= ultima_mov:
                    capturar = False
                    if not completo and i >= 10:
                        break

            # acp_tipo = ''
            acp_esp_div = mov.find_element_by_tag_name('div')
            divs = acp_esp_div.find_elements_by_tag_name('div')
            acp_tipo = divs[0].text
            acp_esp = acp_tipo
            divs.pop(0)
            if len(divs) > 0:
                acp_esp = ''
                for div in divs:
                    acp_esp += ' '+div.text

                acp_esp = acp_esp.strip()

            expand = mov.find_elements_by_partial_link_text('Clique para expandir')
            if len(expand) > 0:
                exp_antes = len(mov.find_element_by_tag_name('div').text)
                expand[0].click()
                inicio = time.time()
                while True:
                    tempoTotal = time.time() - inicio
                    # Verifica se o tempo de resposta excedeu
                    if tempoTotal >= 30:
                        raise MildException("Erro ao expandir texto", self.uf, self.plataforma, self.prc_id)

                    acp_esp = mov.find_element_by_tag_name('div').text
                    if exp_antes != len(acp_esp):
                        break

                # Remove o texto '(Clique para resumir)' do processo
                acp_esp = acp_esp.replace('(Clique para resumir)', '')

            acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp.strip(), 'acp_tipo': acp_tipo}
            if capturar:
                movs.append(acp)

            self.movs.append({**acp, 'novo': capturar})

        return movs

    # CAPTURA AUDIENCIAS DO PROCESSO
    def audiencias(self):
        adcs = []
        for mov in self.movs:
            if not self.completo and not mov['novo']:
                break

            esp = mov['acp_esp'].upper().strip()
            if esp.find('AUDIÊNCIA') != 0:
                continue

            aud = localiza_audiencia(esp, formato_data='%d-%m-%Y %H:%M', formato_re='(\\d+)(\\-)(\\d+)(\\-)(\\d+)(\\s+)(\\d+)(\\:)(\\d+)')
            if not aud:
                continue

            erro = ''
            if 'prp_status' not in aud:
                aud['prp_status'] = 'Agendada'
            if 'prp_tipo' not in aud:
                erro = 'Tipo '

            if erro != '':
                raise MildException("Audiência - "+erro+" não localizado: "+esp, self.uf, self.plataforma, self.prc_id)

            aud['data_mov'] = mov['acp_cadastro']
            adcs.append(aud)

        return adcs

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        '''
        :param str status_atual: Status atual
        '''
        prc = {}

        # LOCALIZA STATUS DO PROCESSO
        prc['prc_status'] = get_status(self.movs, status_atual)

        ul = self.driver.find_elements_by_xpath("//ul[contains(@class, 'resultado-detalhe-item')]")[self.uli]

        prc_numero2 = ul.find_element_by_xpath('uib-accordion/div/div/div[2]/div/h4').text
        prc['prc_numero2'] = localiza_cnj(prc_numero2)
        prc['prc_codigo'] = ajusta_numero(prc['prc_numero2'])

        detalhes = ul.find_elements_by_class_name('result-group')
        for d in detalhes:
            titulo = d.find_element_by_tag_name('label').text
            if titulo == 'Orgão Julgador':
                prc['prc_serventia'] = d.find_element_by_tag_name('div').text

            if titulo == 'Classe CNJ':
                prc_classe = d.find_element_by_tag_name('div').text
                prc['prc_classe'] = prc_classe

            if titulo == 'Assunto(s) CNJ':
                prc['prc_assunto'] = d.find_element_by_tag_name('div').text

        prc['prc_comarca2'] = localiza_comarca(prc['prc_serventia'], self.uf)

        return prc

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo': [], 'passivo': [], 'terceiro': [] }
        nomes = []

        ul = self.driver.find_elements_by_xpath("//ul[contains(@class, 'resultado-detalhe-item')]")[self.uli]
        tabela = ul.find_elements_by_class_name('result-group')
        for tb in tabela:
            polo = ''
            div_polo = tb.find_element_by_tag_name('label').text.strip().upper()

            # if find_string(div_polo,self.titulo_partes['ignorar']):
            #     continue

            if div_polo.upper() == 'REQUERENTE' or div_polo.upper() == 'APELANTE':
                polo = 'ativo' if len(partes['ativo']) == 0 else 'passivo'
            else:
                if find_string(div_polo,self.titulo_partes['ativo']):
                    polo = 'ativo'
                if find_string(div_polo,self.titulo_partes['passivo']):
                    polo = 'passivo'
                if find_string(div_polo, self.titulo_partes['terceiro']):
                    polo = 'terceiro'

            if polo == '':
                continue

            prt_nome = tb.find_element_by_tag_name('div').text
            prt_cpf_cnpj = 'Não Informado'

            if prt_nome == '':
                continue

            if prt_nome in nomes:
                continue
            nomes.append(prt_nome)

            partes[polo].append({'prt_nome': prt_nome.strip(), 'prt_cpf_cnpj': prt_cpf_cnpj})

        if len(partes['ativo']) == 0 or len(partes['passivo']) == 0:
            print(partes)
            raise MildException("Polo não localizado ", self.uf, self.plataforma, self.prc_id)

        return partes

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []
        nomes = []

        ul = self.driver.find_elements_by_xpath("//ul[contains(@class, 'resultado-detalhe-item')]")[self.uli]
        tabela = ul.find_elements_by_class_name('result-group')
        polo = ''
        for tb in tabela:
            div_polo = tb.find_element_by_tag_name('label').text.upper()

            if div_polo.upper() == 'REQUERENTE':
                polo = 'ativo' if len(resps) == 0 else 'passivo'
            else:
                if find_string(div_polo,self.titulo_partes['ativo']):
                    polo = 'Polo Ativo'
                    continue
                if find_string(div_polo,self.titulo_partes['passivo']):
                    polo = 'Polo Passivo'
                    continue

            # if find_string(div_polo,self.titulo_partes['ativo']):
            #     polo = 'Polo Ativo'
            #     continue
            #
            # if find_string(div_polo,self.titulo_partes['passivo']):
            #     polo = 'Polo Passivo'
            #     continue

            if div_polo.upper() != 'ADVOGADO':
                continue

            prr_nome = tb.find_element_by_tag_name('div').text
            if prr_nome == '':
                continue

            if prr_nome in nomes:
                continue
            nomes.append(prr_nome)

            resps.append({'prr_nome': prr_nome, 'prr_cargo': 'Advogado', 'prr_parte': polo})

        return resps

    # AGUARDA ATÉ QUE A ANIMAÇÃO DE LOADING ESTEJA OCULTA
    def wait(self, tempo=50):
        inicio = time.time()
        while True:
            if time.time() - inicio > tempo:
                raise MildException("Loading Timeout", self.uf, self.plataforma, self.prc_id)
            time.sleep(0.5)
            spinner = self.driver.find_element_by_class_name('button-spinner')
            if not spinner:
                break

        return True