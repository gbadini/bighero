from Controllers.Tribunais.Fisico.MG import *
from Controllers.Tribunais.segundo_grau import *

# CLASSE DA VARREDURA DO FISICO DE PE DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE ESAJ2g
class MG2g(SegundoGrau, MG):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "chrome://version/"
        self.pagina_busca = "https://www4.tjmg.jus.br/juridico/sf/proc_massiva2.jsp"
        # self.pagina_processo = "https://www4.tjmg.jus.br/juridico/sf/proc_complemento2.jsp?listaProcessos="
        self.formato_data = '%d/%m/%Y %H:%M'

    # CONFERE SE O CÓDIGO É VALIDO
    def check_codigo(self, codigo):
        '''
        :param str codigo: codigo _GET de acesso
        '''
        if codigo is None:
            return False

        if codigo.strip() == '':
            return False

        return True

    # CONFERE SE OS RECURSOS ESTÃO NA BASE CASO EXISTA MAIS DE UM
    def confere_recursos(self, base, proc):
        recs = self.driver.find_elements_by_xpath('/html/body/div')

        if len(recs) == 1 and proc['rec_codigo'] is not None:
            return True

        achei = True
        if proc['rec_id'] is not None and proc['rec_codigo'] is None:
            for r in recs:
                rec_codigo = r.find_elements_by_partial_link_text('Dados Completos')
                if len(rec_codigo) > 0:
                    rec_codigo = rec_codigo[0].get_attribute('href')
                    parsed = urlparse.urlparse(rec_codigo)
                    parse_qs(parsed.query)
                    url_params = parse_qs(parsed.query)
                    rec_codigo = url_params['listaProcessos'][0]
                    xpaths = (
                        '/html/body/table[1]/tbody/tr[1]/td[2]',
                        '/html/body/table[1]/tbody/tr[1]/td[1]',
                        '/html/body/div[5]/table[1]/tbody/tr[1]/td[2]'
                    )

                    numero_site = 'edfwefewfewf'
                    for xp in xpaths:
                        # print(xp)
                        el = self.driver.find_element_by_xpath(xp)
                        if el:
                            td = el.text
                            break

                    rec_numero = localiza_cnj(td)
                    achei = False
                    Recurso.update_simples(base, proc['rec_id'], {'rec_codigo': rec_codigo, 'rec_numero': rec_numero})
                    break
        else:
            for r in recs:
                td = r.find_elements_by_xpath('table[1]/tbody/tr[1]/td[2]')
                if len(td) == 0:
                    continue
                rec_numero = localiza_cnj(td[0].text)
                link = r.find_element_by_partial_link_text('Dados Completos').get_attribute('href')
                parsed = urlparse.urlparse(link)
                parse_qs(parsed.query)
                url_params = parse_qs(parsed.query)
                rec_codigo = url_params['listaProcessos'][0]
                result = Recurso.select(base, proc['prc_id'], rec_codigo)
                if len(result) == 0:
                    achei = False
                    Recurso.insert(base, {'rec_prc_id': proc['prc_id'], 'rec_codigo': rec_codigo, 'rec_numero': rec_numero,
                                          'rec_plt_id': self.plataforma})


        return achei

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc):
        adc = self.audiencias()
        prt = self.partes()
        adv = self.responsaveis()
        status_atual = 'Ativo' if self.completo else proc['rec_status']
        prc = self.dados(status_atual)

        return adc, prt, prc, adv

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''

        field = self.driver.find_element_by_id('txt_processo_num_unica')
        field.clear()
        field.send_keys(numero_busca[:7])

        field = self.driver.find_element_by_id('dv_num_unica')
        field.clear()
        field.send_keys(numero_busca[7:9])

        field = self.driver.find_element_by_id('ano_num_unica')
        field.clear()
        field.send_keys(numero_busca[9:13])

        field = self.driver.find_element_by_id('comrCodigoNumUnica')
        field.clear()
        field.send_keys(numero_busca[-4:])

        self.driver.find_element_by_id('pesquisarNumeroNumUnica').click()
        self.driver.find_element_by_id('btn_pesquisar').click()

        while True:
            msg_erro = self.driver.find_element_by_xpath('/html/body/p[5]/strong')
            if msg_erro:
                if msg_erro.text.find('Nenhum processo') > -1:
                    return False

            msg_erro = self.driver.find_element_by_xpath('/html/body/h1')
            if msg_erro:
                if msg_erro.text.find('Selecionar comarca') > -1:
                    return False

            recs = self.driver.find_elements_by_xpath('/html/body/div/table[1]/tbody/tr[1]/td[2]')
            if len(recs) > 0:
                return True

        # recs = self.driver.find_elements_by_xpath('/html/body/div/table[1]/tbody')
        # for rec in recs:
        #     rec_numero = rec.find_element_by_xpath('tr[1]/td[2]')
        #     rec_numero = localiza_cnj(rec_numero)
        #     rec_codigo = rec_numero
        #     if len(result) == 0:
        #         achei = False


        return True

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        recs = self.driver.find_elements_by_xpath('/html/body/div')
        for r in recs:
            td = r.find_elements_by_xpath('table[1]/tbody/tr[1]/td[2]')
            if len(td) == 0:
                continue
            cnj_site = localiza_cnj(td[0].text)

            url = r.find_element_by_partial_link_text('Dados Completos').get_attribute('href')
            parsed = urlparse.urlparse(url)
            parse_qs(parsed.query)
            url_params = parse_qs(parsed.query)
            codigo_site = url_params['listaProcessos'][0]
            if codigo_site == codigo:
                r.find_element_by_partial_link_text('Dados Completos').click()
                break

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
            '/html/body/table[1]/tbody/tr[1]/td[2]',
            '/html/body/table[1]/tbody/tr[1]/td[1]',
            '/html/body/div[5]/table[1]/tbody/tr[1]/td[2]'
        )

        numero_site = 'edfwefewfewf'
        for xp in xpaths:
            # print(xp)
            el = self.driver.find_element_by_xpath(xp)
            if el:
                print(el.text)
                cnj = localiza_cnj(el.text, regex="(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\-)(\\d+)(\\/)(\\d+)|([0-9]{17,20})")
                if cnj:
                    numero_site = ajusta_numero(cnj)
                    if numero_busca == numero_site:
                        return True

        raise MildException("Número CNJ Diferente", self.uf, self.plataforma, self.prc_id)

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self, ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        aguarda_presenca_elemento(self.driver, '/html/body/table[8]/tbody/tr[1]/td[3]')
        time.sleep(3)
        acp_esp = self.driver.find_element_by_xpath('/html/body/table[8]/tbody/tr[1]/td[3]').text.strip()
        acp_cad = self.driver.find_element_by_xpath('/html/body/table[8]/tbody/tr[1]/td[2]').text.strip()
        data_cad = datetime.strptime(acp_cad, '%d/%m/%Y')
        return Acompanhamento.compara_mov(base, prc_id, acp_esp, data_cad, self.plataforma, self.grau, rec_id=self.rec_id)

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        '''
        :param str status_atual: Status atual
        '''
        rec = {}
        try_click(self.driver, 'Dados Completos', 'PARTIAL_LINK_TEXT')
        # self.driver.find_element_by_partial_link_text('Dados Completos').click()
        url = self.driver.execute_script('return window.location')
        parsed = urlparse.urlparse(url['href'])
        parse_qs(parsed.query)
        url_params = parse_qs(parsed.query)
        rec['rec_codigo'] = url_params['listaProcessos'][0]

        # LOCALIZA STATUS DO PROCESSO
        rec['rec_status'] = get_status(self.movs, status_atual, grau=2)

        rec_numero = self.driver.find_element_by_xpath('/html/body/table[1]/tbody/tr[1]/td[2]/b').text
        rec_numero = localiza_cnj(rec_numero)
        if rec_numero:
            rec['rec_numero'] = rec_numero

        # self.driver.find_element_by_xpath('/html/body/table[7]/tbody/tr/td[1]/b/a').click()

        campos = {'Valor': 'rec_valor', 'Classe': 'rec_classe', 'Assunto': 'rec_assunto', 'Data Cadastramento': 'rec_distribuicao' }
        trs = self.driver.find_elements_by_xpath('/html/body/table[2]/tbody/tr')
        for tr in trs:
            tds = tr.find_elements_by_tag_name('td')
            if len(tds) > 5:
                continue

            for td in tds:
                titulo = td.find_elements_by_tag_name('b')
                if len(titulo) == 0:
                    continue
                titulo = titulo[0].text
                for c in campos:
                    if titulo.upper().find(c.upper()) > -1:
                        html = td.get_attribute('innerHTML')
                        cnt = html.split('</b>')
                        texto = cnt[1]
                        texto = strip_html_tags(texto)
                        rec[campos[c]] = texto.strip()
                        break

        campos = {'Relator': 'rec_relator', }
        trs = self.driver.find_elements_by_xpath('/html/body/table[3]/tbody/tr[1]')
        for tr in trs:
            tds = tr.find_elements_by_tag_name('td')
            if len(tds) > 5:
                continue

            for td in tds:
                titulo = td.find_elements_by_tag_name('b')
                if len(titulo) == 0:
                    continue
                titulo = titulo[0].text
                for c in campos:
                    if titulo.upper().find(c.upper()) > -1:
                        html = td.get_attribute('innerHTML')
                        cnt = html.split('</b>')
                        texto = cnt[1]
                        texto = strip_html_tags(texto)
                        rec[campos[c]] = texto.strip()
                        break

        if 'rec_distribuicao' in rec:
            r = re.search('(\\d+)(\\/)(\\d+)(\\/)(\\d+)', rec['rec_distribuicao'])
            rec_distribuicao = r.group(0)
            rec['rec_distribuicao'] = datetime.strptime(rec_distribuicao, '%d/%m/%Y')

        return rec