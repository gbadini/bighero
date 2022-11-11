from Controllers.Tribunais.Projudi._projudi_v2 import *
from Config.helpers import *
import urllib.request

# CLASSE DA VARREDURA DO PROJUDI DA BA. HERDA OS METODOS DA CLASSE PROJUDI
class BA(ProjudiV2):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://projudi.tjba.jus.br/projudi/PaginaPrincipal.jsp"
        self.pagina_busca = "https://projudi.tjba.jus.br/projudi/buscas/ProcessosQualquerAdvogado"
        # self.pagina_busca = "https://projudi.tjba.jus.br/projudi/buscas/ProcessosParte"
        # self.pagina_processo = "https://projudi.tjba.jus.br/projudi/listagens/NavegarProcesso?numeroProcesso="
        self.pagina_processo = 'https://projudi.tjba.jus.br/projudi/listagens/DadosProcesso?numeroProcesso='
        # self.pagina_processo = "https://projudi.tjba.jus.br/projudi/listagens/DadosProcesso?consentimentoAcesso=true&numeroProcesso="
        self.reiniciar_navegador = False
        self.arquiva_sentenca = False
        self.wait_loading = False
        self.titulo_partes = get_tipo_partes(grau=2)
        self.tabela_movs = '//*[@id="Arquivos"]/table/tbody/tr/td/table/tbody/tr'
        self.posicao_elementos = {'tipo': 1, 'esp': 2, 'data': 3, 'usr': 4}
        self.formato_data = '%d/%m/%y'
        self.tipo_projudi = 1

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc):
        # return [],{'ativo': [], 'passivo': [], 'terceiro': []},{},[]
        prt = self.partes()
        status_atual = 'Ativo' if self.completo else proc['prc_status']
        prc = self.dados(status_atual)
        adv = self.responsaveis()
        adc = self.audiencias()

        return adc, prt, prc, adv

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

        self.wait_complete()
        inicio = time.time()
        while True:
            if time.time() - inicio > 10:
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

        cnj.click()
        # time.sleep(30)
        return True

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        # time.sleep(60)
        while True:
            try:
                # time.sleep(30)
                if self.driver.find_element_by_xpath('/html/body/strong[2]/p/a'):
                    el = self.driver.find_element_by_xpath('/html/body/strong[1]/p')
                    if el:
                        if el.text.find('Segredo de Justiça') > -1:
                            return True

                if self.driver.find_element_by_xpath('/html/body/center/p'):
                    el = self.driver.find_element_by_xpath('/html/body/center/p')
                    if el:
                        if el.text.find('Você não tem privilégio') > -1:
                            return True

                if self.driver.find_element_by_xpath('//*[@id="Partes"]/table/tbody/tr[1]/td'):
                    break

                if self.driver.find_element_by_xpath('/html/frameset/frameset/frame[1]'):
                    break
            except UnexpectedAlertPresentException:
                try:
                    self.driver.switch_to.alert.accept()
                except NoAlertPresentException:
                    pass

                try:
                    self.driver.execute_script("window.stop();")
                    time.sleep(1)
                    self.driver.execute_script("history.forward()")
                    aguarda_alerta(self.driver, 6)

                    url = self.driver.execute_script('return window.location')
                    parsed = urlparse.urlparse(url['href'])
                    parse_qs(parsed.query)
                    url_params = parse_qs(parsed.query)
                    numeroProcesso = url_params['numeroProcesso'][0]
                    self.driver.get('https://projudi.tjba.jus.br/projudi/listagens/NavegarProcesso?numeroProcesso=' + numeroProcesso)
                except UnexpectedAlertPresentException:
                    self.driver.switch_to.alert.accept()
                    raise MildException("Alerta fora de sincronia", self.uf, self.plataforma, self.prc_id)
                # try:
                #     self.driver.switch_to.alert.accept()
                # except:
                #     pass

        self.confere_cnj(numero_busca)
        return False

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):

        inicio = time.time()
        while True:
            tempoTotal = time.time() - inicio
            if tempoTotal >= 20:
                raise MildException("Última Mov não localizada (frameset)", self.uf, self.plataforma, self.prc_id)

            if self.driver.find_element_by_xpath('/html/frameset/frameset/frame[1]'):
                self.tipo_projudi = 2
                break

            if self.driver.find_element_by_xpath('//*[@id="Partes"]/table/tbody/tr[1]/td/b/font/a'):
                self.tipo_projudi = 1
                break

        if self.tipo_projudi == 1:
            cnj_txt = self.driver.find_element_by_xpath('//*[@id="Partes"]/table/tbody/tr[1]/td/b/font/a').text
        else:
            # time.sleep(5)
            inicio = time.time()
            len_atual = 0
            self.wait_complete()
            while True:
                tempoTotal = time.time() - inicio
                if tempoTotal >= 20:
                    raise MildException("Última Mov não localizada (div)", self.uf, self.plataforma, self.prc_id)

                try:
                    self.driver.switch_to.default_content()
                    if not self.driver.find_element_by_xpath('/html/frameset/frameset/frame[1]'):
                        continue

                    self.driver.switch_to.frame(self.driver.find_element_by_xpath('/html/frameset/frameset/frame[1]'))
                    divs = self.driver.find_elements_by_xpath('/html/body/table/tbody/tr/td/table/tbody/tr[1]/td/div')
                    if len_atual < 2 or len_atual != len(divs):
                        time.sleep(0.5)
                        len_atual = len(divs)
                        continue
                    div = divs[-1]
                    time.sleep(0.5)

                    div.click()
                    self.driver.switch_to.default_content()
                    self.driver.switch_to.frame(self.driver.find_element_by_xpath('/html/frameset/frameset/frame[2]'))
                    self.wait_complete()
                    aguarda_presenca_elemento(self.driver, '/html/body/div/table/tbody/tr[5]/td[2]', tempo=20)
                    if not self.driver.find_element_by_xpath('/html/body/div/table/tbody/tr[5]/td[2]'):
                        raise MildException("Erro ao carregar CNJ na movimentação", self.uf, self.plataforma, self.prc_id)
                    cnj_txt = self.driver.find_element_by_xpath('/html/body/div/table/tbody/tr[5]/td[2]').text

                    if not cnj_txt:
                        raise MildException("Número CNJ não localizado", self.uf, self.plataforma, self.prc_id)

                    if numero_busca != ajusta_numero(cnj_txt):
                        # print(numero_busca, ajusta_numero(cnj_txt))
                        continue

                    self.driver.switch_to.default_content()
                    break
                except (InvalidArgumentException, NoSuchWindowException):
                    # tb = traceback.format_exc()
                    # print(tb)
                    self.driver.switch_to.default_content()
                    pass


        cnj_limpo = ajusta_numero(cnj_txt)
        if cnj_limpo != numero_busca:
            cnj = self.driver.find_element_by_xpath('//*[@id="Partes"]/table/tbody/tr[1]/td/b/font[2]')
            if cnj:
                cnj_limpo = cnj.text.replace('Nº Antigo:','')
                cnj_limpo = ajusta_numero(cnj_limpo.strip())
                if cnj_limpo == numero_busca:
                    return True

            raise MildException("Número CNJ Diferente", self.uf, self.plataforma, self.prc_id)

        return True

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''

        if self.tipo_projudi == 1:
            aguarda_presenca_elemento(self.driver, '//*[@id="Arquivos"]/table/tbody/tr[2]/td/table/tbody/tr/td[3]', tempo=20)
            if not self.driver.find_element_by_xpath('//*[@id="Arquivos"]/table/tbody/tr[2]/td/table/tbody/tr/td[3]'):
                raise MildException("Erro ao carregar movimentação", self.uf, self.plataforma, self.prc_id)
            data_ultima_mov = self.driver.find_element_by_xpath('//*[@id="Arquivos"]/table/tbody/tr[2]/td/table/tbody/tr/td[3]').text
            data_ultima_mov = strip_html_tags(data_ultima_mov)
            data_ultima_mov = data_ultima_mov[:6]+'20'+data_ultima_mov[6:]+' 00:00'
            data_cad = datetime.strptime(data_ultima_mov, '%d/%m/%Y %H:%M')

            acp_tipo = self.driver.find_element_by_xpath('//*[@id="Arquivos"]/table/tbody/tr[2]/td/table/tbody/tr/td[1]').get_attribute('innerHTML')
            acp_tipo = acp_tipo.replace('\r','').replace('\n','').replace('&nbsp;','')

            acp_tipo = strip_html_tags(acp_tipo)
            acp_tipo = acp_tipo.strip()

            return Acompanhamento.compara_mov(base, prc_id, acp_tipo, data_cad, self.plataforma, self.grau, campo='acp_tipo', rec_id=self.rec_id)

        else:
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(self.driver.find_element_by_xpath('/html/frameset/frameset/frame[1]'))
            # self.driver.find_element_by_id('arquivo1').click()
            divs = self.driver.find_elements_by_xpath('/html/body/table/tbody/tr/td/table/tbody/tr[1]/td/div')
            div = divs[-1]
            # div.click()
            tipo = div.text
            f = tipo.find('.')
            acp_tipo = tipo[:f].strip()
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(self.driver.find_element_by_xpath('/html/frameset/frameset/frame[2]'))
            if not aguarda_presenca_elemento(self.driver,'/html/body/div/table/tbody/tr[3]/td[2]'):
                raise MildException("Última mov. não localizada (tipo 2)", self.uf, self.plataforma, self.prc_id)

            data_ultima_mov = self.driver.find_element_by_xpath('/html/body/div/table/tbody/tr[3]/td[2]').text
            data_ultima_mov = strip_html_tags(data_ultima_mov)
            data_ultima_mov = localiza_data(data_ultima_mov)

            return Acompanhamento.compara_mov(base, prc_id, acp_tipo, data_ultima_mov, self.plataforma, self.grau, campo='acp_tipo', rec_id=self.rec_id)

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
        self.wait_complete()
        if self.tipo_projudi == 1:
            table = self.tabela_movs
        else:
            table = '/html/body/table/tbody/tr/td/table/tbody/tr[1]/td/div'
            self.wait_complete()
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(self.driver.find_element_by_xpath('/html/frameset/frameset/frame[1]'))

        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(EC.presence_of_all_elements_located((By.XPATH, table)))
        except TimeoutException:
            raise MildException("Erro ao carregar tabela de movs.", self.uf, self.plataforma, self.prc_id)

        movs = []
        self.movs = []

        movimentos = self.driver.find_elements_by_xpath(table)
        capturar = True
        i = 0
        if len(movimentos) == 0:
            raise MildException("Erro ao capturar tabela de movs.", self.uf, self.plataforma, self.prc_id)
        lista = Acompanhamento.lista_movs(base, prc_id, self.plataforma, acp_grau=self.grau, rec_id=rec_id)
        if self.tipo_projudi == 1:
            movimentos.pop(0)

            for mov in movimentos:
                acps_cadastro = mov.find_elements_by_xpath('td['+str(self.posicao_elementos['data'])+']')
                if len(acps_cadastro) == 0:
                    continue
                acp_tipo = mov.find_element_by_xpath('td[' + str(self.posicao_elementos['tipo']) + ']').text
                acp_tipo = strip_html_tags(acp_tipo)
                acp_cadastro = datetime.strptime(acps_cadastro[0].text, self.formato_data)

                if completo:
                    capturar = True

                acp_esp = mov.find_element_by_xpath('td[' + str(self.posicao_elementos['esp']) + ']').text
                acp_usuario = mov.find_element_by_xpath('td[' + str(self.posicao_elementos['usr']) + ']').text
                acp_esp = strip_html_tags(acp_esp)
                acp_usuario = strip_html_tags(acp_usuario)

                i += 1
                for l in lista:
                    tipo_base = strip_html_tags(l['acp_tipo'])
                    if tipo_base == acp_tipo:
                        # Acompanhamento.update(self.conn_atual, [{'acp_id': l['acp_id'], 'acp_esp': acp_esp.strip(), 'acp_usuario': acp_usuario.strip()}, ])
                        capturar = False
                        break

                if not capturar and not completo and i >= 10:
                    break

                acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp.strip(), 'acp_tipo': acp_tipo.strip(), 'acp_usuario': acp_usuario.strip()}
                if capturar:
                    movs.append(acp)

                self.movs.append({**acp, 'novo': capturar})
        else:
            movimentos.reverse()
            # len_tipo = len(movimentos)
            acp_esp_novo = ''
            acps_cadastro_novo = ''
            acps_cadastro_tmp = ''
            acp_esp_tmp = ''
            # acp_tipo_tmp = ''
            for mov in movimentos:
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(self.driver.find_element_by_xpath('/html/frameset/frameset/frame[1]'))
                cmd = mov.get_attribute('onclick')
                tipo = mov.text
                f = tipo.find('.')
                acp_tipo = tipo[:f].strip()
                # acp_tipo_novo = tipo[f+1:].strip()
                self.driver.execute_script(cmd)

                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(self.driver.find_element_by_xpath('/html/frameset/frameset/frame[2]'))
                self.wait_complete()
                aguarda_presenca_elemento(self.driver, '/html/body/div/table/tbody/tr[3]/td[2]')
                inicio = time.time()
                while acp_esp_tmp == acp_esp_novo and acps_cadastro_tmp == acps_cadastro_novo:
                    if time.time() - inicio > 10:
                        break
                    # if time.time() - inicio > 40:
                    #     raise MildException("Erro ao carregar movimentação", self.uf, self.plataforma, self.prc_id, False)
                    try:
                        acp_esp_novo = self.driver.find_element_by_xpath('/html/body/div/table/tbody/tr[2]/td[2]').get_attribute('innerHTML')
                        acps_cadastro_novo = self.driver.find_element_by_xpath('/html/body/div/table/tbody/tr[3]/td[2]').text
                    except:
                        continue

                acps_cadastro_tmp = acps_cadastro_novo
                acp_esp_tmp = acp_esp_novo
                # acp_tipo_tmp = acp_tipo_novo
                acps_cadastro = strip_html_tags(acps_cadastro_tmp)
                acps_cadastro = localiza_data(acps_cadastro)
                acp_cadastro = datetime.strptime(acps_cadastro, '%Y-%m-%d')

                acp_esp = acp_esp_tmp.split('\n')
                esp = ''
                for a in acp_esp:
                    if a.strip() == '':
                        continue
                    tmp = strip_html_tags(a)
                    esp += ' '+tmp.strip()

                acp_usuario = self.driver.find_element_by_xpath('/html/body/div/table/tbody/tr[4]/td[2]').text
                # tipo = mov.text

                # acp_tipo = str(len_tipo)
                # len_tipo -= 1
                if completo:
                    capturar = True

                i += 1
                for l in lista:
                    tipo_base = strip_html_tags(l['acp_tipo'])
                    if acp_cadastro == l['acp_cadastro'] and tipo_base == acp_tipo:
                        # Acompanhamento.update(self.conn_atual, [{'acp_id': l['acp_id'], 'acp_esp': esp.strip(), 'acp_usuario': acp_usuario},])
                        capturar = False
                        break

                if not capturar and not completo and i >= 10:
                    break

                # acp_usuario = mov.find_element_by_xpath('td[' + str(self.posicao_elementos['usr']) + ']').text
                # acp_usuario = strip_html_tags(acp_usuario)

                acp = {'acp_cadastro': acp_cadastro, 'acp_esp': esp.strip(), 'acp_tipo': acp_tipo.strip(), 'acp_usuario': acp_usuario.strip()}
                if capturar:
                    movs.append(acp)

                self.movs.append({**acp, 'novo': capturar})

        return movs

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        if self.tipo_projudi == 2:
            return []

        return super().responsaveis()

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        if self.tipo_projudi == 1:
            return super().partes()
        else:
            url = self.driver.execute_script('return window.location')
            parsed = urlparse.urlparse(url['href'])
            parse_qs(parsed.query)
            url_params = parse_qs(parsed.query)
            numeroProcesso = url_params['numeroProcesso'][0]
            self.driver.get('https://projudi.tjba.jus.br/projudi/listagens/ResumoProcesso?numeroProcesso=' + numeroProcesso)
            self.wait_complete()
            partes = {'ativo': [], 'passivo': [], 'terceiro': []}
            nomes = []

            trs = self.driver.find_elements_by_xpath('/html/body/font/table[1]/tbody/tr')
            for tr in trs:
                tb = tr.find_elements_by_xpath('td[2]/font/table/tbody/tr[2]/td[3]')
                if len(tb) == 0:
                    continue
                tipo_parte_txt = tr.find_element_by_xpath('td[1]').text
                achei = False

                for polo in self.titulo_partes:
                    if find_string(tipo_parte_txt, self.titulo_partes[polo]):
                        achei = True
                        if polo == 'ignorar':
                            break

                        tb_partes = tr.find_elements_by_xpath('td[2]/font/table/tbody/tr')
                        tb_partes.pop(0)

                        for p in tb_partes:
                            try:
                                prt_nome = p.find_element_by_xpath('td[1]').text.strip()
                            except:
                                continue
                            if prt_nome in nomes:
                                continue
                            nomes.append(prt_nome)
                            try:
                                prt_cpf_cnpj = p.find_element_by_xpath('td[3]').text.strip()
                            except:
                                continue

                            if prt_cpf_cnpj == 'Não Cadastrado' or prt_cpf_cnpj == '':
                                prt_cpf_cnpj = 'Não Informado'
                            partes[polo].append({'prt_nome': prt_nome.strip(), 'prt_cpf_cnpj': prt_cpf_cnpj})
                        break

                if not achei:
                    raise MildException("polo vazio " + tipo_parte_txt, self.uf, self.plataforma, self.prc_id)

            return partes


    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):

        if self.tipo_projudi == 1:
            return super().dados(status_atual)
        else:
            prc = {}

            erro = self.driver.find_element_by_xpath('/html/body/center/font/h4[1]')
            if erro:
                if erro.text.find('Ocorreu um erro ao executar a funcionalidade solicitada.') > -1:
                    return prc

            if status_atual == 'Segredo de Justiça':
                status_atual = 'Ativo'
            # LOCALIZA STATUS DO PROCESSO
            prc['prc_status'] = get_status(self.movs, status_atual, self.arquiva_sentenca)
            campos = {'Juízo': 'prc_juizo', 'Assunto': 'prc_assunto', 'Classe': 'prc_classe', 'Segredo': 'prc_segredo','Fase': 'prc_fase', 'Distribuição': 'prc_distribuicao','Valor da Causa': 'prc_valor_causa'}

            tables = self.driver.find_elements_by_xpath('/html/body/font/table[1]/tbody/tr')
            i = 0
            for tb in tables:
                i += 1
                tds = tb.find_elements_by_tag_name('td')
                if len(tds) > 5:
                    continue

                j = 1
                for td in tds:
                    j += 1
                    if j % 2 == 1:
                        continue

                    titulo = td.text
                    for c in campos:
                        if titulo.upper().find(c.upper()) > -1:
                            txt = self.driver.find_element_by_xpath('/html/body/font/table[1]/tbody/tr[' + str(i) + ']/td[' + str(j) + ']')
                            if txt:
                                prc[campos[c]] = txt.text
                            break

            if 'prc_juizo' not in prc:
                raise MildException("Juízo não localizado: ", self.uf, self.plataforma, self.prc_id)

            prts = prc['prc_juizo'].split('Juiz:')

            if len(prts) == 1:
                prts = prc['prc_juizo'].split('Juiz Titular:')

            if len(prts) == 1:
                prts = prc['prc_juizo'].split('Juiz Responsável:')

            prc['prc_juizo'] = strip_html_tags(prts[0].strip())

            prc['prc_serventia'] = prc['prc_juizo']

            prc['prc_comarca2'] = localiza_comarca(prc['prc_juizo'], self.uf)

            if 'prc_distribuicao' in prc:
                prc_distribuicao = localiza_data(prc['prc_distribuicao'], localiza_hora=True)
                prc['prc_distribuicao'] = datetime.strptime(prc_distribuicao, '%Y-%m-%d %H:%M')

            if 'prc_segredo' in prc:
                prc['prc_segredo'] = False if prc['prc_segredo'].find('NÃO') > -1 else True

            prc_numero2 = self.driver.find_element_by_xpath('/html/body/font/table[1]/tbody/tr[1]/td')
            prc_numero2 = localiza_cnj(prc_numero2.text, "(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(.)([0-9]{4})(\\.)(\\d+)(\\.)(\\d+)(\\-)(\\d+)")

            prc['prc_numero2'] = prc_numero2
            prc['prc_terceiro'] = True
            url = self.driver.execute_script('return window.location')
            parsed = urlparse.urlparse(url['href'])
            parse_qs(parsed.query)
            url_params = parse_qs(parsed.query)
            prc['prc_codigo'] = url_params['numeroProcesso'][0]

            return prc

        # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS

    # CAPTURA AUDIENCIAS DO PROCESSO
    def audiencias(self):
        adcs = []
        movs = self.movs[:]
        movs.reverse()
        for mov in movs:
            if not self.completo and not mov['novo']:
                break

            esp = mov['acp_esp'].upper().strip()
            if esp.find('AUDIÊNCIA') != 0 or esp == 'AUDIÊNCIA':
                continue

            r = re.search("(\\d+)(\\s+)(de)(\\s+)([A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÍÏÓÔÕÖÚÇÑ]+)(\\s+)(de)(\\s+)(\\d+)(\\s+)(às)(\\s+)(\\d+)(\\:)(\\d+)", esp, re.IGNORECASE | re.DOTALL)
            if r is None:
                continue

            reg_data = r.group(0)
            data_padrao = localiza_data(esp, True)
            esp = esp.replace(reg_data, data_padrao)
            aud = localiza_audiencia(esp, formato_data='%Y-%m-%d %H:%M', formato_re='(\\d+)(\\-)(\\d+)(\\-)(\\d+)(\\s+)(\\d+)(\\:)(\\d+)')
            if not aud:
                continue

            erro = ''
            if 'prp_status' not in aud:
                erro = 'Status'
            if 'prp_tipo' not in aud:
                erro = 'Tipo'

            if erro != '':
                raise MildException("Audiência - "+erro+" não localizado: "+esp, self.uf, self.plataforma, self.prc_id)

            serventia = None
            p = esp.find('(AGENDADA PARA')
            if p > -1:
                esp_spl = esp.split(',')
                if len(esp_spl) > 1:
                    serventia = esp_spl[1][3:-1].strip()
            aud['prp_serventia'] = serventia
            aud['data_mov'] = mov['acp_cadastro']
            adcs.append(aud)

        url = self.driver.execute_script('return window.location')
        parsed = urlparse.urlparse(url['href'])
        parse_qs(parsed.query)
        url_params = parse_qs(parsed.query)
        numeroProcesso = url_params['numeroProcesso'][0]
        self.driver.get('https://projudi.tjba.jus.br/projudi/VerLotacaoAudiencia?numeroProcesso=' + numeroProcesso)
        varrer = False
        inicio = time.time()
        self.wait_complete()
        while True:
            if time.time() - inicio > 30:
                self.driver.execute_script("window.stop();")
                raise MildException("Loading Timeout (audiencia)", self.uf, self.plataforma, self.prc_id, False)

            if aguarda_alerta(self.driver, aceitar=True, tempo=0.5):
                break

            if aguarda_presenca_elemento(self.driver, 'login', tipo='ID', tempo=0.5):
                break

            if aguarda_presenca_elemento(self.driver, '/html/body/div/table/tbody/tr[1]/td', tempo=1):
                varrer = True
                break

        if varrer:
            if not aguarda_presenca_elemento(self.driver, '/html/body/div/table/tbody/tr[1]/td'):
                raise MildException("Erro ao carregar dados da audiencia", self.uf, self.plataforma, self.prc_id)
            tr_data = self.driver.find_element_by_xpath('/html/body/div/table/tbody/tr[1]/td').text.replace(' às ',' ')
            tr_tipo = self.driver.find_element_by_xpath('/html/body/div/table/tbody/tr[2]/td').text
            tr_modalidade = self.driver.find_element_by_xpath('/html/body/div/table/tbody/tr[3]/td').text
            esp_aud = tr_data + ' ' + tr_tipo + ' ' + tr_modalidade
            aud = localiza_audiencia(esp_aud, formato_data='%d/%m/%y %H:%M', formato_re='(\\d+)(\\/)(\\d+)(\\/)(\\d+)(\\s+)(\\d+)(\\:)(\\d+)')
            if aud:
                aud['prp_status'] = 'Designada'
                aud['data_mov'] = datetime.now()

                tr_4_1 = self.driver.find_element_by_xpath('/html/body/div/table/tbody/tr[4]/td/table/tbody/tr[1]/td')
                if tr_4_1:
                    tr_4_1 = self.driver.find_element_by_xpath('/html/body/div/table/tbody/tr[4]/td/table/tbody/tr[1]/td').text
                    dp = tr_4_1.find(':')
                    endereco = tr_4_1[dp + 1:].strip()
                    tr_4_2 = self.driver.find_element_by_xpath('/html/body/div/table/tbody/tr[4]/td/table/tbody/tr[2]/td').text
                    dp = tr_4_2.find(':')
                    aud['prp_serventia'] = endereco + ' ' + tr_4_2[dp + 1:].strip()
                else:
                    tr_4_1 = self.driver.find_element_by_xpath('/html/body/div/table/tbody/tr[4]/td').text
                    dp = tr_4_1.find(':')
                    aud['prp_serventia'] = tr_4_1[dp + 1:].strip()

                for ad in adcs[:]:
                    if aud['prp_data'] == ad['prp_data']:
                        aud['data_mov'] = ad['data_mov']
                        adcs.remove(ad)
                        break

                adcs.append(aud)
        self.driver.back()
        return adcs

    def download(self, prc_id, arquivos_base, pendentes, pasta_intermediaria):
        # return []
        # Verifica a existencia de captcha
        if self.tipo_projudi != 1 or  self.tipo == 2:
            return []
        arquivos = []
        # Clica no link "Navegar pelo processo"
        aguarda_presenca_elemento(self.driver, 'Navegar pelo Processo', tipo='PARTIAL_LINK_TEXT')
        self.driver.find_element_by_partial_link_text('Navegar pelo Processo').click()
        # self.driver.find_element_by_partial_link_text('/html/body/p[2]/a[1]').click()
        # Aguarda o carregamento total da pagina
        self.wait_complete()
        # Alterna para o iframe "menu"
        self.driver.switch_to.frame('menu')
        # Aguarda o carregamento total da tabela de movimentações
        table = '/html/body/table/tbody/tr/td/table/tbody/tr[1]/td/div'
        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(EC.presence_of_all_elements_located((By.XPATH, table)))
        except TimeoutException:
            raise MildException("Erro ao carregar tabela de movs.", self.uf, self.plataforma, self.prc_id)
        # Retorna a quantidade de tds do menu lateral
        tds_menu = self.driver.find_elements_by_xpath('/html/body/table/tbody/tr')
        ultimo_arquivo = ''
        # Iteração nas tds do menu lateral
        # Faz contagem regressiva, buscando do item maior para o menor
        for en_menu in range(len(tds_menu), 0, -1):
            tds = self.driver.find_elements_by_xpath(
                '/html/body/table/tbody/tr[' + str(en_menu) + ']/td/table/tbody/tr')
            # Verifica se contem sub-itens, o primeiro item da td não contém arquivo para baixar
            # Não precisa capturar os detalhes da movimentação se não tiver arquivos vinculados
            if len(tds) == 1:
                continue
            # Iteração nos sub-itens
            for en_item, td in enumerate(tds):
                arq = {'pra_prc_id': prc_id, 'pra_plt_id': self.plataforma, 'pra_erro': False,
                       'pra_arquivo': None, 'pra_sigilo': False, 'pra_original': None, 'pra_tentativas': None,
                       'pra_excluido': False}
                item = self.driver.find_element_by_xpath('/html/body/table/tbody/tr[' + str(en_menu) + ']/td/table/tbody/tr' + '[' + str(en_item + 1) + ']/td/div')
                # Separa o ID e texto do item
                # print(item.text)
                txt_item = item.text.split(' ', 1)
                id_item = txt_item[0]
                descricao_item = txt_item[1] if len(txt_item) > 1 else ''

                # Se o arquivo não constar na base realiza o download
                if en_item > 0:
                    achei = False
                    for a_b in arquivos_base:
                        # Verifica se o ID TJ já existe na base
                        if a_b['pra_id_tj'] == id_item:  # arq['pra_id_tj']:
                            achei = True
                            # Se o arquivo existe na base, verifica se existe pendências
                            if len(pendentes) == 0:
                                return arquivos
                            # Se o arquivo existir na lista de pendências recebe o valor salvo na base
                            # Realiza o download e remove da lista de pendentes
                            for p, pend in enumerate(pendentes[:]):
                                if pend['pra_id_tj'] == id_item:  # arq['pra_id_tj']:
                                    achei = False
                                    arq['pra_tentativas'] = pend['pra_tentativas']
                                    arq['pra_id'] = pend['pra_id']
                                    # Apaga o item atual da lista das pendências
                                    del pendentes[p]
                                    break
                            break
                    # Se o arquivo constar na base e não constar na lista de pendências
                    if achei:
                        continue
                # Clica no Item do menu
                item.click()
                # Aguarda o carregamento total da pagina
                self.wait_complete()
                # Alterna para o frame principal
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame('principal')
                # O item 0 é o titulo "Detalhes da movimentação"
                if en_item == 0:
                    # Detalhes da movimentação
                    arq['pra_id_tj'] = id_item
                    aguarda_presenca_elemento(self.driver, '/html/body/div/table/tbody/tr[2]/td[2]')
                    pra_descricao = self.driver.find_element_by_xpath('/html/body/div/table/tbody/tr[2]/td[2]').text
                    data_tj = self.driver.find_element_by_xpath('/html/body/div/table/tbody/tr[3]/td[2]').text
                    # Formata a data no padrão SQL
                    pra_data = localiza_data(data_tj, localiza_hora=True)
                    pra_data = datetime.strptime(pra_data, '%Y-%m-%d %H:%M')
                    arq['pra_data'] = pra_data
                    pra_usuario = self.driver.find_element_by_xpath('/html/body/div/table/tbody/tr[4]/td[2]').text
                    arq['pra_usuario'] = pra_usuario
                    # Retorna para frame "menu"
                    self.driver.switch_to.default_content()
                    self.driver.switch_to.frame('menu')
                    continue
                arq['pra_id_tj'] = id_item
                arq['pra_descricao'] = descricao_item + ' - ' + pra_descricao
                arq['pra_data'] = pra_data
                arq['pra_usuario'] = pra_usuario
                # Aguarda o carregamento total da pagina
                self.wait_complete()
                inicio = time.time()
                arquivo_atual = ultimo_arquivo
                while ultimo_arquivo == arquivo_atual:
                    if time.time() - inicio > 40:
                        raise MildException("Erro ao carregar página do arquivo", self.uf, self.plataforma,self.prc_id)
                    try:
                        arquivo_atual = self.driver.find_element_by_xpath('/html/body/iframe').get_attribute('src')
                    except:
                        time.sleep(2)

                ultimo_arquivo = arquivo_atual

                # Alterna para o iframe dentro do frame
                try:
                    self.driver.switch_to.frame(self.driver.find_element_by_xpath('/html/body/iframe'))
                except:
                    time.sleep(2)
                    self.driver.switch_to.frame(self.driver.find_element_by_xpath('/html/body/iframe'))

                limpar_pasta(self.pasta_download)
                # Verifica se a existe a classe 'pdf' para baixar o PDF
                if self.driver.find_element_by_class_name('pdf'):
                    # Clica no botão 'Abrir'
                    aguarda_presenca_elemento(self.driver, 'open-button', tipo='ID')
                    self.driver.find_element_by_id('open-button').click()
                # Verifica se o conteúdo tem vídeo/áudio
                elif self.driver.find_element_by_xpath('/html/body/video/source'):
                    video = self.driver.find_element_by_xpath('/html/body/video/source')
                    video_url = video.get_property('src')
                    # Insere um link via Javascript para poder clicar e baixar o video ou audio
                    self.driver.execute_script(""" var a = document.createElement('a');
                                                   var linkText = document.createTextNode('download');
                                                   a.appendChild(linkText);
                                                   a.href = '""" + video_url + """';
                                                    a.id = 'link_download_video';
                                                    a.download = true;
                                                   document.body.appendChild(a);""")
                    aguarda_presenca_elemento(self.driver, 'link_download_video', tipo='ID')
                    self.driver.find_element_by_id('link_download_video').click()
                # Se não possuir a classe 'pdf' só tem visualizador e printa a tela
                else:
                    if not self.driver.find_element_by_class_name('tituloPagina'):
                        self.driver.execute_script('setTimeout(function() { window.print(); }, 0);')
                    else:
                        # Em alguns visualizadores aparece a mensagem 'Download do arquivo não permitido'
                        arq['pra_sigilo'] = True
                if not arq['pra_sigilo']:
                    if not aguarda_download(self.pasta_download, 1, tempo=40):
                        open_button = self.driver.find_element_by_id('open-button')
                        if open_button:
                            open_button.click()
                            arq['pra_erro'] = False if aguarda_download(self.pasta_download, 1, tempo=40) else True
                        else:
                            arq['pra_erro'] = True
                    else:
                        arq['pra_erro'] = False

                if not arq['pra_erro'] and not arq['pra_excluido'] and not arq['pra_sigilo']:
                    file_names = os.listdir(self.pasta_download)
                    # Remove os caracteres excedentes caso o arquivo original tenha mais de 100
                    arq['pra_original'] = file_names[0][:100]
                    pra_arquivo = trata_arquivo(file_names[0], self.pasta_download, pasta_intermediaria)
                    arq['pra_arquivo'] = pra_arquivo
                elif self.tipo != 2 and arq['pra_erro']:
                    arq['pra_original'] = None
                    arq['pra_arquivo'] = None
                    arq['pra_tentativas'] = 1 if arq['pra_tentativas'] is None else arq['pra_tentativas'] + 1
                    limpar_pasta(self.pasta_download)
                    print('Erro download ', arq)
                arquivos.append(arq)
                # Retorna para frame 'menu'
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame('menu')
        arquivos.reverse()
        return arquivos

    def wait_complete(self):
        page_state = ''
        inicio = time.time()
        while page_state != 'complete':
            time.sleep(0.5)
            if time.time() - inicio > 40:
                self.driver.execute_script("window.stop();")
                raise MildException("Loading Timeout", self.uf, self.plataforma, self.prc_id, False)
            try:
                page_state = self.driver.execute_script('return document.readyState;')
            except:
                pass


    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def confere_arquivos_novos(self, arquivos_base):
        if self.tipo_projudi == 2:
            return False

        return True
