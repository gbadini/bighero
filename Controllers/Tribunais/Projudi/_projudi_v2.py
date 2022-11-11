from Controllers.Tribunais.Projudi._projudi import *
from Config.helpers import *


# CLASSE DA VARREDURA DO PROJUDI SEGUNDA VERSAO. HERDA OS METODOS DA CLASSE PROJUDI
class ProjudiV2(Projudi):

    def __init__(self):
        super().__init__()
        self.tabela_movs = '//*[@id="Arquivos"]/table/tbody/tr/td/table/tbody/tr[1]'
        self.posicao_elementos = {'tipo': 3, 'esp': 4, 'data': 5, 'usr': 7}
        self.formato_data = '%d/%m/%Y %H:%M'
        self.remover_primeira_tr = True
        self.limpar_com_backspace = False
        self.xpath_menu = '//*[@id="BarraMenu"]/div'

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''
        aguarda_presenca_elemento(self.driver, 'login', tipo='ID')

        try_click(self.driver, '/html/body/div[4]/div[1]/a')

        self.driver.find_element_by_id("login").send_keys(usuario)
        self.driver.find_element_by_id("senha").send_keys(senha)
        self.driver.find_element_by_id("senha").send_keys(Keys.ENTER)

        if not aguarda_presenca_elemento(self.driver, self.xpath_menu):
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
        captchaimg = self.driver.find_element_by_id('captchaimg')
        if captchaimg:
            v = self.driver.find_element_by_xpath('//*[@id="corpo"]/form/table/tbody/tr[2]/td[2]/input').get_attribute('value').strip()
            while len(v) < 5:
                if time.time() - inicio > 60:
                    raise CriticalException("Captcha Detectado", self.uf, self.plataforma, self.prc_id, False)
                v = self.driver.find_element_by_xpath('//*[@id="corpo"]/form/table/tbody/tr[2]/td[2]/input').get_attribute('value').strip()
                time.sleep(1)


        self.driver.find_element_by_id('numeroProcesso').clear()
        if self.limpar_com_backspace:
            for r in range(0,20):
                self.driver.find_element_by_id("numeroProcesso").send_keys(Keys.BACKSPACE)

        self.driver.find_element_by_id('numeroProcesso').send_keys(numero_busca)

        id_nome_parte_input = self.driver.find_element_by_id('id_nome_parte')
        if id_nome_parte_input:
            id_nome_parte_input.click()
            id_nome_parte = self.driver.find_element_by_id('id_nome_parte').get_attribute('value')

            if id_nome_parte.strip() != '':
                return False

        self.driver.find_element_by_id("numeroProcesso").send_keys(Keys.ENTER)
        listagem = localiza_elementos(self.driver, ('/html/body/div[1]/form[2]/table/tbody/tr[4]/td[2]/a', '/html/body/div[3]/div/div[1]/form[2]/table/tbody/tr[4]/td[2]/a', '/html/body/div[1]/form[2]/table/tbody/tr[2]/td[1]/a','//*[@id="corpo"]/div[1]/form[2]/table/tbody/tr[4]/td[2]/a'))
        if listagem:
            numero_site = localiza_cnj(listagem.text, regex="(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\-)(\\d+)")
            numero_site = ajusta_numero(numero_site)
            if numero_busca != numero_site:
                return False
            listagem.click()
            if aguarda_alerta(self.driver, 0.1, aceitar=False, rejeitar=False):
                alert = self.driver.switch_to.alert
                if alert.text.find('cumprir Intima') > -1:
                    prc_data = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    Processo.update_simples(self.active_conn, self.prc_id, {'prc_data_projudi': prc_data})
                alert.accept()
            return True

        return False

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        try:
            aguarda_presenca_elemento(self.driver, '//*[@id="Partes"]/table/tbody/tr[1]/td')
        except UnexpectedAlertPresentException:
            return True

        self.confere_cnj(numero_busca)

        return False

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        cnjs = self.driver.find_elements_by_xpath('//*[@id="Partes"]/table/tbody/tr[1]/td')
        for cnj_txt in cnjs:
            cnj = cnj_txt.text

            cnj = localiza_cnj(cnj, "(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(.)([0-9]{4})(\\.)(\\d+)(\\.)(\\d+)(\\-)(\\d+)")
            if not cnj:
                continue
            cnj_limpo = ajusta_numero(cnj)
            if cnj_limpo == numero_busca:
                return True

        # print("Número CNJ Diferente")
        # time.sleep(9999)
        raise MildException("Número CNJ Diferente", self.uf, self.plataforma, self.prc_id)

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''

        data_ultima_mov = self.driver.find_element_by_xpath('//*[@id="Arquivos"]/table/tbody/tr[2]/td/table/tbody/tr[1]/td['+str(self.posicao_elementos['data'])+']').text
        data_ultima_mov = strip_html_tags(data_ultima_mov)

        data_tj = datetime.strptime(data_ultima_mov, self.formato_data)
        if ultima_data == data_tj:
            return True

        return False

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo': [], 'passivo': [], 'terceiro': []}
        nomes = []

        trs = self.driver.find_elements_by_xpath('//*[@id="Partes"]/table/tbody/tr')
        for tr in trs:
            tb = tr.find_elements_by_xpath('td[2]/table/tbody/tr[2]/td[5]')
            if len(tb) == 0:
                continue
            tipo_parte_txt = tr.find_element_by_xpath('td[1]').text
            achei = False

            for polo in self.titulo_partes:
                if find_string(tipo_parte_txt, self.titulo_partes[polo]):
                    achei = True
                    if polo == 'ignorar':
                        break
                    tb_partes = tr.find_elements_by_xpath('td[2]/table/tbody/tr')
                    tb_partes.pop(0)
                    for p in tb_partes:
                        try:
                            prt_nome = p.find_element_by_xpath('td[2]').text.strip()
                        except:
                            continue
                        if prt_nome in nomes:
                            continue
                        nomes.append(prt_nome)

                        prt_cpf_cnpj = p.find_element_by_xpath('td[4]').text.strip()
                        if prt_cpf_cnpj == 'Não Cadastrado' or prt_cpf_cnpj == '':
                            prt_cpf_cnpj = 'Não Informado'
                        partes[polo].append({'prt_nome': prt_nome.strip(), 'prt_cpf_cnpj': prt_cpf_cnpj})
                    break

            if not achei:
                raise MildException("polo vazio " + tipo_parte_txt, self.uf, self.plataforma, self.prc_id)

        return partes

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []
        id_tb = 3
        i = 0
        trs = self.driver.find_elements_by_xpath('//*[@id="Partes"]/table/tbody/tr/td[2]/table')
        for tr in trs:
            i += 1
            links = tr.find_elements_by_xpath('tbody/tr/td[5]/a')
            for link in links:
                href = link.get_attribute('href')
                f = href.find("mostraOculta('")
                id_tr = href[f + 14:]
                f = id_tr.find("',")
                id_tr = id_tr[:f]
                if not self.driver.find_elements_by_id('trAdv'+id_tr):
                    id_tb = i
                    self.driver.execute_script(href)

        wait = WebDriverWait(self.driver, 2)
        try:
            wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="Partes"]/table/tbody/tr['+str(id_tb)+']/td[2]/table/tbody/tr[3]/td/table')))
        except TimeoutException:
            id2 = int(id_tb) + 1
            wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="Partes"]/table/tbody/tr[' + str(id2) + ']/td[2]/table/tbody/tr[3]/td/table')))


        trs = self.driver.find_elements_by_xpath('//*[@id="Partes"]/table/tbody/tr')
        for tr in trs:
            tb = tr.find_elements_by_xpath('td[2]/table/tbody/tr[2]/td[5]')
            if len(tb) == 0:
                continue
            tipo_parte_txt = tr.find_element_by_xpath('td[1]').text
            for polo in self.titulo_partes:
                if find_string(tipo_parte_txt, self.titulo_partes[polo]):
                    if polo == 'ignorar':
                        break

                    tr_advs  = tr.find_elements_by_xpath('td[2]/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr')
                    for tra in tr_advs:
                        prr_oab = tra.find_elements_by_xpath('td[2]')
                        if len(prr_oab) == 0:
                            continue

                        prr_nome = tra.find_element_by_xpath('td[1]').text

                        if prr_nome == 'Nome' or find_string(prr_nome, ('Histórico de Advogados', 'Advogado não cadastrado','Nenhum advogado')):
                            continue

                        f = prr_nome.find('(CPF')
                        if f > -1:
                            prr_nome = prr_nome[:f].strip()

                        polo_adv = 'Polo Ativo' if polo=='ativo' else 'Polo Passivo'
                        resps.append({'prr_nome': prr_nome, 'prr_oab': prr_oab[0].text, 'prr_cargo': 'Advogado', 'prr_parte': polo_adv})

                    break


        trs = self.driver.find_elements_by_xpath('//*[@id="Partes"]/table/tbody/tr')
        for tr in trs:
            td1 = tr.find_elements_by_xpath('td[1]')
            if len(td1) == 0:
                continue
            txt = td1[0].text
            if txt == 'Juízo:':
                cont = tr.find_element_by_xpath('td[2]').text
                prts = cont.split('Juiz:')
                if len(prts) == 1:
                    prts = cont.split('Juiz Titular:')
                prr_nome = prts[1].replace('Histórico de Juízes','')
                if prr_nome.upper().find('DESIGNADO') == -1:
                    resps.append({'prr_nome': prr_nome.strip(), 'prr_oab': '', 'prr_cargo': 'Juiz', 'prr_parte': ''})
                break

        return resps

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        prc = {}

        # LOCALIZA STATUS DO PROCESSO
        if status_atual == 'Segredo de Justiça':
            status_atual = 'Ativo'
        prc['prc_status'] = get_status(self.movs, status_atual, self.arquiva_sentenca)
        campos = {'Juízo': 'prc_juizo', 'Assunto': 'prc_assunto', 'Classe': 'prc_classe', 'Segredo': 'prc_segredo','Fase': 'prc_fase', 'Distribuição': 'prc_distribuicao','Valor da Causa': 'prc_valor_causa'}

        tables = self.driver.find_elements_by_xpath('//*[@id="Partes"]/table')
        tb_i = 0
        for tb in tables:
            trs = tb.find_elements_by_xpath('tbody/tr')
            tb_i += 1
            i = 0
            for tr in trs:
                i += 1
                # if i <= 4:
                #     continue

                tds = tr.find_elements_by_tag_name('td')
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
                            txt = self.driver.find_element_by_xpath('//*[@id="Partes"]/table['+str(tb_i)+']/tbody/tr[' + str(i) + ']/td[' + str(j) + ']')
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

        prc['prc_juizo'] = prts[0].strip()

        prc['prc_serventia'] = prc['prc_juizo']

        prc['prc_comarca2'] = localiza_comarca(prc['prc_juizo'], self.uf)

        if 'prc_distribuicao' in prc:
            prc_distribuicao = localiza_data(prc['prc_distribuicao'], localiza_hora=True)
            prc['prc_distribuicao'] = datetime.strptime(prc_distribuicao, '%Y-%m-%d %H:%M')

        if 'prc_segredo' in prc:
            prc['prc_segredo'] = False if prc['prc_segredo'].find('NÃO') > -1 else True

        prc_numero2 = self.driver.find_element_by_xpath('//*[@id="Partes"]/table/tbody/tr[1]/td/b/font/a')
        if prc_numero2:
            prc_numero2 = prc_numero2.text
        else:
            cnjs = self.driver.find_elements_by_xpath('//*[@id="Partes"]/table/tbody/tr[1]/td')
            for cnj_txt in cnjs:
                cnj = cnj_txt.text

                prc_numero2 = localiza_cnj(cnj, "(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(.)([0-9]{4})(\\.)(\\d+)(\\.)(\\d+)(\\-)(\\d+)")
                if prc_numero2:
                    break

        prc['prc_numero2'] = prc_numero2

        url = self.driver.execute_script('return window.location')
        parsed = urlparse.urlparse(url['href'])
        parse_qs(parsed.query)
        url_params = parse_qs(parsed.query)
        prc['prc_codigo'] = url_params['numeroProcesso'][0]

        return prc

    # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS
    def download(self, prc_id, arquivos_base, pendentes, pasta_intermediaria):
        return []