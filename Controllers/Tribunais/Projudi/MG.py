from Controllers.Tribunais.Projudi._projudi_v2 import *


# CLASSE DA VARREDURA DO PROJUDI DE MG. HERDA OS METODOS DA CLASSE PROJUDIV2
class MG(ProjudiV2):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://projudi.tjmg.jus.br/projudi/PaginaPrincipal.jsp"
        self.pagina_busca = "https://projudi.tjmg.jus.br/projudi/buscas/ProcessosQualquerAdvogado"
        self.pagina_processo = "https://projudi.tjmg.jus.br/projudi/listagens/DadosProcesso?numeroProcesso="
        self.posicao_elementos = {'tipo': 1, 'esp': 2, 'data': 3, 'usr': 4}

    # CONFERE SE O CÓDIGO É VALIDO
    def check_codigo(self, codigo):
        '''
        :param str codigo: codigo _GET de acesso
        '''
        if codigo is None:
            return False

        if codigo.strip() == '':
            return False

        if codigo.find('txtProcesso') > -1:
            return False

        return True

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):

        cnjs = self.driver.find_elements_by_xpath('/html/body/div[4]/table/tbody/tr/td[12]/table/tbody/tr[2]/td/span')
        for cnj_txt in cnjs:
            cnj = cnj_txt.text

            cnj = localiza_cnj(cnj, "(\\d+)(.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(.)([0-9]{4})(\\.)(\\d+)(\\.)(\\d+)(\\-)(\\d+)")
            if not cnj:
                continue
            cnj_limpo = ajusta_numero(cnj)
            if cnj_limpo == numero_busca:
                return True

        raise MildException("Número CNJ Diferente", self.uf, self.plataforma, self.prc_id)

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        prc = {}

        # LOCALIZA STATUS DO PROCESSO
        prc['prc_status'] = get_status(self.movs, status_atual)
        campos = {'Juízo': 'prc_juizo', 'Assunto': 'prc_assunto', 'Classe': 'prc_classe', 'Segredo': 'prc_segredo','Fase': 'prc_fase', 'Distribuição': 'prc_distribuicao','Valor da Causa': 'prc_valor_causa'}

        trs = self.driver.find_elements_by_xpath('/html/body/form[8]/div[1]/table/tbody/tr')
        i = 1
        for tr in trs:
            i += 1
            tds = tr.find_elements_by_xpath('td/b')
            if len(tds) == 0:
                continue

            j = 0
            for td in tds:
                j += 1

                titulo = td.text
                for c in campos:
                    if titulo.upper().find(c.upper()) > -1:
                        txt = self.driver.find_element_by_xpath('/html/body/form[8]/div[1]/table/tbody/tr[' + str(i) + ']/td[' + str(j) + ']')
                        if txt:
                            prc[campos[c]] = txt.text
                        break

        if 'prc_juizo' not in prc:
            raise MildException("Juízo não localizado: ", self.uf, self.plataforma, self.prc_id)

        prts = prc['prc_juizo'].split('Juiz:')

        if len(prts) == 1:
            prts = prc['prc_juizo'].split('Juiz Titular:')

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
            cnjs = self.driver.find_elements_by_xpath('/html/body/div[4]/table/tbody/tr/td[12]/table/tbody/tr[2]/td/span')
            for cnj_txt in cnjs:
                cnj = cnj_txt.text

                prc_numero2 = localiza_cnj(cnj, "(\\d+)(.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(.)([0-9]{4})(\\.)(\\d+)(\\.)(\\d+)(\\-)(\\d+)")
                if prc_numero2:
                    break

        prc['prc_numero2'] = prc_numero2

        url = self.driver.execute_script('return window.location')
        parsed = urlparse.urlparse(url['href'])
        parse_qs(parsed.query)
        url_params = parse_qs(parsed.query)
        prc['prc_codigo'] = url_params['numeroProcesso'][0]

        return prc