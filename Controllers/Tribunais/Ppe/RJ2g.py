import time

from Controllers.Tribunais.Ppe.RJ import *
from Controllers.Tribunais.segundo_grau import *

# CLASSE DA VARREDURA DO PPE DO RJ DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE PPE2g
class RJ2g(SegundoGrau, RJ):

    def __init__(self):
        super().__init__()
        # self.pagina_busca = 'https://www3.tjrj.jus.br/portalservicos/#/consproc/consultaportal'
        self.pagina_busca = ''
        self.pagina_processo = ''

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''

        if not aguarda_presenca_elemento(self.driver,'//*[@id="corpo"]/app-iframe/section/iframe', tempo=30):
            raise MildException("Erro ao carregar página de busca", self.uf, self.plataforma, self.prc_id, False)

        if not aguarda_presenca_elemento(self.driver,'//*[@id="corpo"]/app-iframe/section/iframe', tempo=30):
            raise MildException("Erro ao carregar página de busca", self.uf, self.plataforma, self.prc_id, False)

        iframe_processo = self.driver.find_element_by_xpath('//*[@id="corpo"]/app-iframe/section/iframe')
        self.driver.switch_to_frame(iframe_processo)


        titulo = self.driver.find_element_by_xpath('//*[@id="conteudo"]/span/table[1]/tbody/tr[4]/td/h2')
        if titulo:
            self.driver.execute_script('javascript:history.go(-1);')
        # try_click(self.driver, '//*[@id="content-barra"]/a[1]')

        if not aguarda_presenca_elemento(self.driver,'//*[@id="porNumero"]/div[1]/div/app-codigo-processo-origem/div/div[2]/div/div/input[1]', tempo=45):
            raise MildException("Erro ao carregar página de busca", self.uf, self.plataforma, self.prc_id, False)

        self.wait_load()
        field = self.driver.find_element_by_xpath('//*[@id="porNumero"]/div[1]/div/app-codigo-processo-origem/div/div[2]/div/div/input[1]')
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

        return True

    # CONFERE SE OS RECURSOS ESTÃO NA BASE CASO EXISTA MAIS DE UM
    def confere_recursos(self, base, proc):
        recs = self.driver.find_elements_by_xpath('//*[@id="form"]/table/tbody/tr/td/ul/li/a')

        if len(recs) <= 1:
            return True

        achei = True
        for rec in recs:
            rec_url = rec.get_attribute('href').strip()
            if rec_url.find('?N=') == -1:
                continue

            parsed = urlparse.urlparse(rec_url)
            parse_qs(parsed.query)
            url_params = parse_qs(parsed.query)
            rec_codigo = url_params['N'][0]

            rec_numero = rec.text
            rec_numero = localiza_cnj(rec_numero)
            result = Recurso.select(base, proc['prc_id'], rec_codigo)
            if len(result) == 0:
                achei = False
                Recurso.insert(base, {'rec_prc_id': proc['prc_id'], 'rec_codigo': rec_codigo, 'rec_numero': rec_numero,
                                      'rec_plt_id': self.plataforma})

        return achei

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):

        while True:
            if self.driver.find_elements_by_xpath('//*[@id="porNumero"]/div[3]/div/p-table/div/div/table/tbody/tr/td[1]/a'):
                break

            if self.driver.find_elements_by_xpath('//*[@id="pdf"]/div/div[2]/div[2]/div[1]'):
                break

            if self.driver.find_elements_by_xpath('//*[@id="conteudo"]/span/table[1]/tbody/tr[4]/td/h2'):
                break

        if not self.driver.find_elements_by_xpath('//*[@id="conteudo"]/span/table[1]/tbody/tr[4]/td/h2'):
            time.sleep(1)
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            links = self.driver.find_elements_by_xpath('//*[@id="porNumero"]/div[3]/div/p-table/div/div/table/tbody/tr/td[1]/a')
            while len(links) < 1:
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

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        iframe_processo = self.driver.find_element_by_xpath('//*[@id="corpo"]/app-iframe/section/iframe')
        if iframe_processo:
            self.driver.switch_to_frame(iframe_processo)

        self.wait_load()
        if not aguarda_presenca_elemento(self.driver, '//*[@id="conteudo"]/span/table[1]/tbody/tr[4]/td/h2'):
            raise MildException("Captcha Solicitado", self.uf, self.plataforma, self.prc_id)

        n = self.driver.find_element_by_xpath('//*[@id="conteudo"]/span/table[1]/tbody/tr[4]/td/h2')
        # if not n:
        #     raise MildException("Captcha Solicitado", self.uf, self.plataforma, self.prc_id)

        n = n.text
        n1 = localiza_cnj(n)
        n1 = ajusta_numero(n1)
        if n1 != numero_busca:
            raise MildException("CNJ diferente na busca", self.uf, self.plataforma, self.prc_id, False)

        return True

     # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        '''
        :param str status_atual: Status atual
        '''
        rec = {}
        rec['rec_status'] = get_status(self.movs, status_atual, grau=2)
        n = self.driver.find_element_by_xpath('//*[@id="content"]/form/table/tbody/tr[3]/td/h2')
        if not n:
            n = self.driver.find_element_by_xpath('//*[@id="conteudo"]/span/table[1]/tbody/tr[4]/td/h2')

        rec['rec_numero'] = localiza_cnj(n.text)
        campos = {'Classe': 'rec_classe', 'Assunto': 'rec_assunto', 'AGTE': 'rec_recorrente', 'AGDO': 'rec_recorrido', 'APELANTE': 'rec_recorrente', 'RECORRIDO': 'rec_recorrido', 'RECORRENTE': 'rec_recorrente', 'APELADO': 'rec_recorrido','Órgão Julgador': 'rec_orgao','Relator': 'rec_relator', }

        linhas = self.driver.find_elements_by_xpath('//*[@id="content"]/form/table/tbody/tr')
        if len(linhas) == 0:
            linhas = self.driver.find_elements_by_xpath('//*[@id="conteudo"]/span/table/tbody/tr')

        url = self.driver.execute_script('return window.location')
        parsed = urlparse.urlparse(url['href'])
        parse_qs(parsed.query)
        url_params = parse_qs(parsed.query)
        # print(url_params)
        rec['rec_codigo'] = url_params['N'][0]

        for linha in linhas:
            tds = linha.find_elements_by_xpath('td')
            if len(tds) != 2:
                continue

            titulo = tds[0].text
            conteudo = tds[1].text
            for cmp in campos:
                if titulo.upper().find(cmp.upper()) > -1:
                    rec[campos[cmp]] = conteudo.strip()
                    break

            if find_string(linha.find_element_by_xpath('td[1]').text, ('Listar todos os personagens','Processo originário')):
                break

        return rec

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        prts = {'ativo':[], 'passivo':[], 'terceiro':[]}
        return prts

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []
        return resps

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

        return True