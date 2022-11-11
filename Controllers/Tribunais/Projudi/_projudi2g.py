from Controllers.Tribunais.Projudi._projudi import *
from Controllers.Tribunais.segundo_grau import *
# from Models.recursoModel import *
import time


# CLASSE DA VARREDURA DO PJE DE SEGUNDO GRAU. HERDA OS METODOS DAS CLASSES PLATAFORMA e PJE
class Projudi2g(SegundoGrau, Projudi):

    def __init__(self):
        super().__init__()
        self.plataforma = 3
        self.movs = []
        self.tabela_movs = '//*[@id="tabprefix2"]/div/div/table/tbody/tr'

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc):
        adc = self.audiencias()
        prt = self.partes()
        adv = self.responsaveis()
        status_atual = 'Ativo' if self.completo else proc['rec_status']
        prc = self.dados(status_atual)

        return adc, prt, prc, adv

    # CONFERE SE OS RECURSOS ESTÃO NA BASE CASO EXISTA MAIS DE UM
    def confere_recursos(self, base, proc):
        recs = self.driver.find_elements_by_xpath('//*[@id="buscaProcessosQualquerInstanciaForm"]/table[2]/tbody/tr/td[2]/a')

        if len(recs) == 1 and proc['rec_codigo'] is not None:
            return True

        achei = True
        if proc['rec_id'] is not None and proc['rec_codigo'] is None:
            if len(recs) == 0:
                sj = self.driver.find_element_by_xpath('//*[@id="buscaProcessosQualquerInstanciaForm"]/table[2]/tbody/tr/td[3]')
                if sj:
                    if sj.text.find('Segredo de Justiça') > -1:
                        Recurso.update_simples(base, proc['rec_id'], {'rec_status': 'Segredo de Justiça', 'rec_data_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
                        return False

            rec_codigo = recs[0].text
            rec_numero = localiza_cnj(rec_codigo)
            achei = False
            Recurso.update_simples(base, proc['rec_id'], {'rec_codigo': rec_codigo, 'rec_numero': rec_numero})
        else:
            for rec in recs:
                rec_codigo = rec.text
                rec_numero = localiza_cnj(rec_codigo)
                result = Recurso.select(base, proc['prc_id'], rec_codigo)
                if len(result) == 0:
                    achei = False
                    Recurso.insert(base, {'rec_prc_id': proc['prc_id'], 'rec_codigo': rec_codigo, 'rec_numero': rec_numero,
                                          'rec_plt_id': self.plataforma})

        return achei

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''
        self.driver.find_element_by_id("login").send_keys(usuario)
        self.driver.find_element_by_id("senha").send_keys(senha)
        self.driver.find_element_by_id("senha").send_keys(Keys.ENTER)

        if not aguarda_presenca_elemento(self.driver, 'BarraMenu', tipo='ID'):
            return False

        # self.driver.find_element_by_xpath('//*[@id="main-menu"]/li[8]/a').click()
        self.driver.find_element_by_partial_link_text('Buscas').click()
        time.sleep(1)
        # self.driver.find_element_by_xpath('//*[@id="main-menu"]/li[8]/a').click()
        # aguarda_presenca_elemento(self.driver, '//*[@id="main-menu"]/li[8]/ul/li[2]/a')
        # self.driver.find_element_by_xpath('//*[@id="main-menu"]/li[8]/ul/li[2]/a').click()
        url = self.driver.find_element_by_partial_link_text('Processos 2º Grau').get_attribute('href')

        self.pagina_busca = url
        return True

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        # el = self.driver.find_element_by_xpath('//*[@id="buscaProcessosQualquerInstanciaForm"]/table[2]/tbody/tr/td[3]')
        # if el:
        #     if el.text.find('Segredo de Justiça') > -1:
        #         return True

        # self.confere_cnj(numero_busca)

        trs = self.driver.find_elements_by_xpath('//*[@id="buscaProcessosQualquerInstanciaForm"]/table[2]/tbody/tr')
        for tr in trs:
            td3 = tr.find_element_by_xpath('td[3]')
            if td3:
                if td3.text.find('Segredo de Justiça') > -1:
                    return True

            td2 = tr.find_element_by_xpath('td[2]/a')
            if td2.text == codigo:
                url = td2.get_attribute('href')
                self.driver.execute_script("window.open('" + url + "', '_self')")
                return False

        raise FatalException("Processo não autuado" , self.uf, self.plataforma, self.prc_id)
        # return False

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo': [], 'passivo': [], 'terceiro': []}
        nomes = []
        self.driver.execute_script("setTab('/projudi#', 'tabPartes', 'prefix', 1, false); ")
        # self.driver.find_element_by_xpath('//*[@id="tabItemprefix2"]/div[2]/a').click()

        tabela = self.driver.find_elements_by_xpath('//*[@id="includeContent"]/table')
        self.driver.execute_script("window.scrollTo( 0, 0 );")
        i = 0
        tipos = {'ativo': 'X', 'passivo': 'Y', 'terceiro': 'Z'}
        for tb in tabela:
            i += 1
            tipo_parte_txt = self.driver.find_element_by_xpath('//*[@id="includeContent"]/h4['+str(i)+']')
            if not tipo_parte_txt:
                continue
            tipo_parte_txt = tipo_parte_txt.text
            achei = False
            for polo in self.titulo_partes:
                if find_string(tipo_parte_txt, self.titulo_partes[polo]):
                    achei = True
                    if polo == 'ignorar':
                        break

                    lista = tb.find_elements_by_xpath('tbody/tr')
                    # polo = 'ativo' if i == 0 else 'passivo'

                    for l in lista:
                        td4 = l.find_elements_by_xpath('td[4]')
                        if len(td4) == 0:
                            continue

                        prt_nome = l.find_element_by_xpath('td[2]').text
                        prt_nome = prt_nome.replace('(em Recuperação Judicial)', '')

                        p = prt_nome.find('(citação')
                        if p > -1:
                            prt_nome = prt_nome[:p-1]

                        p = prt_nome.find('representad')
                        if p > -1:
                            prt_nome = prt_nome[:p-1]

                        if prt_nome in nomes:
                            continue
                        nomes.append(prt_nome)

                        prt_cpf_cnpj = td4[0].text
                        if prt_cpf_cnpj == 'Não Cadastrado':
                            prt_cpf_cnpj = 'Não Informado'

                        partes[polo].append({'prt_nome': prt_nome.strip(), 'prt_cpf_cnpj': prt_cpf_cnpj})

                    break

            if not achei:
                raise MildException("polo vazio " + tipo_parte_txt, self.uf, self.plataforma, self.prc_id)

        if tipos['ativo'] == tipos['passivo']:
            return {'ativo': [{'prt_nome': 'AMBOS',}, ],}

        return partes

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        rec = {}

        self.confere_sub_processos()
        rec['rec_status'] = get_status(self.movs, status_atual, grau=2)

        rec_numero = self.driver.find_element_by_xpath('//*[@id="recursoForm"]/h3').text
        rec_numero = localiza_cnj(rec_numero)
        rec['rec_numero'] = rec_numero

        campos = {'Classe Processual': 'rec_classe', 'Assunto Principal': 'rec_assunto', 'Nível de Sigilo': 'rec_segredo', 'Relator': 'rec_relator', 'Órgão Julgador': 'rec_orgao'}
        trs = self.driver.find_elements_by_xpath('//*[@id="recursoForm"]/fieldset/table[1]/tbody/tr')
        for tr in trs:
            tds = tr.find_elements_by_xpath('td[1]')
            if len(tds) == 0:
                continue

            titulo = tds[0].text
            for c in campos:
                if titulo.upper().find(c.upper()) > -1:
                    rec[campos[c]] = tr.find_element_by_xpath('td[2]').text

        if 'rec_segredo' in rec:
            rec['rec_segredo'] = False if rec['rec_segredo'].find('Público') > -1 else True

        campos = {'Valor da': 'rec_valor', 'Distribuição': 'rec_distribuicao'}

        trs = self.driver.find_elements_by_xpath('//*[@id="tabprefix0"]/fieldset/table/tbody/tr')
        i = 0
        for tr in trs:
            i += 1
            tds = tr.find_elements_by_tag_name('td')
            j = 1
            for td in tds:
                j += 1
                label = td.find_elements_by_tag_name('label')
                if len(label) == 0:
                    continue
                titulo = td.text

                for c in campos:
                    if titulo.upper().find(c.upper()) > -1:
                        rec[campos[c]] = self.driver.find_element_by_xpath(
                            '//*[@id="tabprefix0"]/fieldset/table/tbody/tr[' + str(i) + ']/td[' + str(j) + ']').text
                        break

        if 'rec_distribuicao' in rec:
            if rec['rec_distribuicao'].strip() == '':
                del rec['rec_distribuicao']
            else:
                r = re.search('(\\d+)(\\/)(\\d+)(\\/)(\\d+)', rec['rec_distribuicao'])
                if r is not None:
                    rec_distribuicao = r.group(0)
                    rec['rec_distribuicao'] = datetime.strptime(rec_distribuicao, '%d/%m/%Y')
                else:
                    del rec['rec_distribuicao']

        return rec
