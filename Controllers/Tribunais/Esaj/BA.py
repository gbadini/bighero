from Controllers.Tribunais.Esaj._esaj import *
from Config.helpers import *

# CLASSE DA VARREDURA DO ESAJ DA BA. HERDA OS METODOS DA CLASSE ESAJ
class BA(Esaj):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "http://esaj.tjba.jus.br/sajcas/login?service=http%3A//esaj.tjba.jus.br/esaj/portal.do%3Fservico%3D740000"
        self.pagina_busca = "http://esaj.tjba.jus.br/cpopg/openMobile.do"
        self.pagina_processo = "http://esaj.tjba.jus.br/cpopg/showMobile.do?processo.codigo="
        self.url_base = "http://esaj.tjba.jus.br/"
        self.id_mensagem_erro = 'spwTabelaMensagem'
        self.download_click = True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        try_click(self.driver, 'conpassButtonClose', tipo='ID')

        self.driver.find_element_by_xpath('//*[@id="NUMPROC"]/label/input').clear()
        self.driver.find_element_by_xpath('//*[@id="NUMPROC"]/label/input').send_keys(numero_busca)
        self.driver.find_element_by_xpath('//*[@id="NUMPROC"]/label/input').send_keys(Keys.ENTER)

        try_click(self.driver, '//*[@id="conpass-tag"]/div/div[2]/div[1]')

        if self.driver.find_element_by_id(self.id_mensagem_erro):
            txt = self.driver.find_element_by_id(self.id_mensagem_erro).text
            if find_string(txt, ('deve ser preenchido', 'Não existem informações disponíveis', 'Não foi possível obter',)):
                return False

        return True

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        try:
            txt = self.driver.find_element_by_xpath('//*[@id="blocoDados"]/ul/li[1]/span').text
            txt = strip_html_tags(txt).strip()
            if txt == '':
                return True
        except:
            pass

        self.confere_cnj(numero_busca)
        return False

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
            '/html/body/table[4]/tbody/tr/td/table[2]/tbody/tr[1]/td[2]/table/tbody/tr/td/span[1]',
            '/html/body/div/table[4]/tbody/tr/td/div[1]/table[2]/tbody/tr[1]/td[2]/table/tbody/tr/td/span[1]',
            '//*[@id="blocoDados"]/ul/li[1]/span'
        )

        for xp in xpaths:
            el = self.driver.find_element_by_xpath(xp)
            if el:
                cnj = localiza_cnj(el.text)
                if cnj:
                    numero_site = ajusta_numero(cnj)
                    if numero_busca == numero_site:
                        return True

        if self.driver.find_element_by_id(self.id_mensagem_erro):
            txt = self.driver.find_element_by_id(self.id_mensagem_erro).text
            if find_string(txt, ('deve ser preenchido', 'Não existem informações disponíveis', 'Não foi possível obter',)):
                raise FatalException("Processo Migrado", self.uf, self.plataforma, self.prc_id)

        raise MildException("Número CNJ Diferente", self.uf, self.plataforma, self.prc_id)

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        self.driver.find_element_by_id('blocoMovimentacoes').click()
        if not aguarda_presenca_elemento(self.driver, '//*[@id="blocoMovimentacoes"]/ul/li[1]', aguarda_visibilidade=True):
            raise MildException("Última Mov não localizada", self.uf, self.plataforma, self.prc_id)

        mov = self.driver.find_element_by_xpath('//*[@id="blocoMovimentacoes"]/ul/li[1]')
        mov_text = mov.text
        if mov_text.upper().find('NÃO FORAM ENCONTRADAS MOVIMENTAÇÕES') > -1:
            return False

        acp_cad = mov_text[:10].strip()
        acp_cad = acp_cad.replace('&nbsp;', '').replace("\r", '').replace("\n", '')
        data_cad = datetime.strptime(acp_cad, '%d/%m/%Y')

        links = mov.find_elements_by_xpath('a')
        acp_esp = ''
        if len(links) > 0:
            links[0].click()
            inicio = time.time()
            while acp_esp == '':
                if time.time() - inicio > 20:
                    raise MildException("Erro ao carregar esp", self.uf, self.plataforma, self.prc_id)
                acp_esp = mov.find_element_by_xpath('span').text
                if acp_esp == 'Movimentação não possui complemento.':
                    acp_esp = ''

        if acp_esp == '':
            acp_esp = mov_text[10:].strip()

        acp_esp = acp_esp.replace('&nbsp;', '').replace("\r", '').replace("\n", '').replace('<arquivo>', '').replace('<<arquivo>', '')

        return Acompanhamento.compara_mov(base, prc_id, acp_esp, data_cad, self.plataforma, self.grau, rec_id=self.rec_id)

    # CAPTURA ACOMPANHAMENTOS DO PROCESSO
    def acompanhamentos(self, proc_data, completo, base):
        '''
        :param datetime Última movimentação registrada na base
        :param bool Realiza a captura completa das movimentações
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        self.movs = []
        movs = []
        prc_id = proc_data['prc_id']
        rec_id = proc_data['rec_id'] if 'rec_id' in proc_data else None

        if not self.driver.find_element_by_xpath('//*[@id="blocoMovimentacoes"]/ul/li[1]'):
            self.driver.find_element_by_id('blocoMovimentacoes').click()
            if not aguarda_presenca_elemento(self.driver, '//*[@id="blocoMovimentacoes"]/ul/li[1]', aguarda_visibilidade=True):
                raise MildException("Última Mov não localizada", self.uf, self.plataforma, self.prc_id)

        self.driver.execute_script("window.scrollTo(0,0);")
        self.driver.find_element_by_id('blocoPartes').click()
        self.driver.execute_script("window.scrollTo(0,0);")
        self.driver.find_element_by_id('blocoAudiencias').click()
        self.driver.execute_script("window.scrollTo(0,0);")
        self.driver.find_element_by_id('blocoPartes').click()

        movimentos = self.driver.find_elements_by_xpath('//*[@id="blocoMovimentacoes"]/ul/li')
        if try_click(self.driver, 'linkTodasMovimentacoes', tipo='CLASS_NAME'):
            movimentos2 = self.driver.find_elements_by_xpath('//*[@id="blocoMovimentacoes"]/ul/li')
            inicio = time.time()
            while len(movimentos) >= len(movimentos2):
                movimentos2 = self.driver.find_elements_by_xpath('//*[@id="blocoMovimentacoes"]/ul/li')
                if time.time() - inicio > 20:
                    raise MildException("Erro ao carregar lista de movs", self.uf, self.plataforma, self.prc_id)
            movimentos = movimentos2

        if movimentos[0].text.upper().find('NÃO FORAM ENCONTRADAS MOVIMENTAÇÕES') > -1:
            return []

        # BUSCA MOVIMENTAÇÕES DO PROCESSO NA BASE
        lista = Acompanhamento.lista_movs(base, prc_id, self.plataforma, acp_grau=self.grau, rec_id=rec_id)
        capturar = True
        i = 0
        for mov in movimentos:
            i += 1
            acp_txt = mov.text
            acp_txt = acp_txt.replace('&nbsp;', '').replace("\r", '').replace("\n", '')
            acp_cadastro = acp_txt[:10].strip()
            acp_cadastro = acp_cadastro.replace('&nbsp;','').replace("\r", '').replace("\n",'')
            r = re.search('(\\d+)(\\/)(\\d+)(\\/)(\\d+)', acp_cadastro)
            if not r:
                continue

            acp_cadastro = datetime.strptime(r.group(0) + ' 00:00:00', '%d/%m/%Y %H:%M:%S')

            links = mov.find_elements_by_xpath('a')
            acp_tipo = acp_txt[10:].strip()
            acp_esp = ''
            if len(links) > 0:
                links[0].click()
                inicio = time.time()
                while acp_esp == '':
                    if time.time() - inicio > 10:
                        links[0].click()

                    if time.time() - inicio > 20:
                        # print("Erro ao carregar esp ", links[0].text)
                        # time.sleep(999)
                        raise MildException("Erro ao carregar esp", self.uf, self.plataforma, self.prc_id)
                    acp_esp = mov.find_element_by_xpath('span').text
                    if acp_esp == 'Movimentação não possui complemento.':
                        acp_esp = ''

            if acp_esp == '':
                acp_esp = acp_tipo
            acp_esp = acp_esp.replace('<arquivo>','').replace('<<arquivo>','').replace('&nbsp;','').replace("\r", '').replace("\n",'')

            if completo:
                capturar = True

            esp_site = corta_string(acp_esp)
            for l in lista:
                esp_base = corta_string(l['acp_esp'])

                if acp_cadastro == l['acp_cadastro'] and esp_site == esp_base:
                    capturar = False
                    break

            if not capturar and not completo and i >= 10:
                break

            acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp, 'acp_tipo': acp_tipo}
            if capturar:
                movs.append(acp)

            self.movs.append({**acp, 'novo': capturar})

        if len(self.movs) == 0:
            raise MildException("Erro ao capturar Movs", self.uf, self.plataforma, self.prc_id)
        # print('acp ', movs)
        return movs

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        prc = {}
        self.driver.execute_script("window.scrollTo(0,0);")

        # LOCALIZA STATUS DO PROCESSO
        prc['prc_status'] = get_status(self.movs, status_atual)
        lis = self.driver.find_elements_by_xpath('//*[@id="blocoDados"]/ul/li')

        campos = {'Número:': 'prc_numero2', 'Assunto': 'prc_assunto', 'Classe': 'prc_classe', 'Distr.': 'prc_serventia',  'Distribuição': 'prc_distribuicao', 'Vl. ação': 'prc_valor_causa',}

        i = 1
        for li in lis:
            i += 1
            try:
                label = li.find_element_by_tag_name('label').text
            except:
                continue

            if label.strip() == '':
                continue

            for c in campos:
                if label.upper().find(c.upper()) > -1:
                    prc[campos[c]] = li.find_element_by_tag_name('span').text
                    break

        prc['prc_comarca2'] = localiza_comarca(prc['prc_serventia'], self.uf)
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

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo': [], 'passivo': [], 'terceiro':[]}

        lis = self.driver.find_elements_by_xpath('//*[@id="blocoPartes"]/ul/li')
        if try_click(self.driver, '//*[@id="blocoPartes"]/ul/li[5]/a', tipo='XPATH'):
            lis2 = self.driver.find_elements_by_xpath('//*[@id="blocoPartes"]/ul/li')
            inicio = time.time()
            while len(lis) >= len(lis2):
                lis2 = self.driver.find_elements_by_xpath('//*[@id="blocoPartes"]/ul/li')
                if time.time() - inicio > 10:
                    if not self.driver.find_element_by_xpath('//*[@id="blocoPartes"]/ul/li[5]/a'):
                        break
                    raise MildException("Erro ao carregar lista de partes", self.uf, self.plataforma, self.prc_id)
            lis = lis2

        ul = self.driver.find_elements_by_xpath('//*[@id="blocoPartes"]/ul/li')

        if len(ul) == 0:
            raise MildException('ul partes vazio', self.uf, self.plataforma, self.prc_id)

        nomes = []
        for li in ul:
            polo = ''
            label = li.find_elements_by_tag_name('label')
            if len(label) == 0:
                continue

            label = label[0].text
            if find_string(label,self.titulo_partes['ignorar']):
                continue

            if find_string(label,self.titulo_partes['ativo']):
                polo = 'ativo'
            if find_string(label,self.titulo_partes['passivo']):
                polo = 'passivo'
            if find_string(label,self.titulo_partes['terceiro']):
                polo = 'terceiro'

            if polo == '':
                raise MildException("polo vazio "+label, self.uf, self.plataforma, self.prc_id)

            prt_nome = li.find_element_by_tag_name('span').text
            if not find_string(label,('ADVOGADO:','ADVOGADA:','Def. Público','Defª. Pública:','Defensor',)):
                if prt_nome in nomes:
                    continue
                nomes.append(prt_nome)
                partes[polo].append({'prt_nome': prt_nome, 'prt_cpf_cnpj': 'Não Informado'})

        return partes

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []

        ul = self.driver.find_elements_by_xpath('//*[@id="blocoPartes"]/ul/li')

        nomes = []
        polo = ''
        for li in ul:
            labels = li.find_elements_by_tag_name('label')

            if len(labels) == 0:
                continue

            i = -1
            for label in labels:
                i += 2
                lbl_txt = label.text
                if find_string(lbl_txt,self.titulo_partes['ativo']):
                    polo = 'Polo Ativo'
                if find_string(lbl_txt,self.titulo_partes['passivo']):
                    polo = 'Polo Passivo'

                if not find_string(lbl_txt, ('ADVOGADO:', 'ADVOGADA:', 'Def. Público','Defª. Pública:','Defensor',)):
                    continue

                if polo == '':
                    raise MildException("polo vazio", self.uf, self.plataforma, self.prc_id)

                prr_nome = li.find_elements_by_xpath('span['+str(i)+']')
                if len(prr_nome) == 0:
                    continue
                prr_nome = prr_nome[0].text
                if prr_nome in nomes:
                    continue
                nomes.append(prr_nome)
                resps.append({'prr_nome': prr_nome, 'prr_oab': None, 'prr_cargo': 'Advogado', 'prr_parte': polo})

        return resps

    # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS
    # def download(self, prc_id, arquivos_base, pendentes, pasta_intermediaria):
    #     arquivos = []
    #     return arquivos