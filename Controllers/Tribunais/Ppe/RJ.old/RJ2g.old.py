from Controllers.Tribunais.Ppe.RJ import *
from Controllers.Tribunais.segundo_grau import *

# CLASSE DA VARREDURA DO PPE DO RJ DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE PPE2g
class RJ2g(SegundoGrau, RJ):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://www3.tjrj.jus.br/segweb/faces/login.jsp?indGet=true&SIGLASISTEMA=PORTALSERVICOS"
        self.pagina_busca = 'http://www4.tjrj.jus.br/ConsultaUnificada/consulta.do#tabs-numero-indice0'
        self.pagina_processo = 'http://www4.tjrj.jus.br/ejud/ConsultaProcesso.aspx?N='

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

        # CAPTURA ACOMPANHAMENTOS DO PROCESSO

    def acompanhamentos(self, proc_data, completo, base):
        '''
        :param datetime Última movimentação registrada na base
        :param bool Realiza a captura completa das movimentações
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        print('acps')
        prc_id = proc_data['prc_id']
        rec_id = proc_data['rec_id'] if 'rec_id' in proc_data else None
        movs = []
        self.movs = []

        if self.grau == 1:
            self.insert_recursos(base, proc_data)

        lista = Acompanhamento.lista_movs(base, prc_id, self.plataforma, acp_grau=self.grau, rec_id=rec_id)

        btn = self.driver.find_element_by_xpath('//*[@id="content-barra"]/a[5]')
        if btn:
            movimentos1 = self.driver.find_elements_by_xpath('//*[@id="content"]/form/table/tbody/tr')
            movimentos2 = self.driver.find_elements_by_xpath('//*[@id="Movimentos"]/span/table/tbody/tr')
            btn.click()
            while True:
                temp_len1 = self.driver.find_elements_by_xpath('//*[@id="content"]/form/table/tbody/tr')
                temp_len2 = self.driver.find_elements_by_xpath('//*[@id="Movimentos"]/span/table/tbody/tr')
                if len(movimentos1) != len(temp_len1) or len(movimentos2) != len(temp_len2):
                    break

        i = 0
        movimentos = []
        movimentos0 = self.driver.find_elements_by_xpath('//*[@id="content"]/form/table/tbody/tr')
        if len(movimentos0) > 0:
            movimentos.append(self.driver.find_elements_by_xpath('//*[@id="content"]/form/table/tbody/tr'))
        else:
            movimentos.append(self.driver.find_elements_by_xpath('//*[@id="conteudo"]/span/table/tbody/tr'))
            movimentos.append(self.driver.find_elements_by_xpath('//*[@id="Movimentos"]/span/table/tbody/tr'))

        for movimento in movimentos:
            acp_cadastro = None
            acp_esp = ''
            acp_tipo = ''
            novo = False
            x = 0
            while True:
                if len(movimento) == 0:
                    break
                if movimento[-1].text.strip() == '':
                    del movimento[-1]
                else:
                    break

            for linha in movimento:
                x += 1
                if len(linha.find_elements_by_id('Movimentos')) > 0:
                    x = len(movimento)

                chaves = ('Tipo do Movimento', 'FASE ATUAL:', 'FASE:', 'Processo(s) no Conselho Recursal',
                          'Processo(s) no Tribunal de Justiça:', 'PUBLICAÇÃO DO ACÓRDÃO', 'INTEIRO TEOR',
                          'SESSAO DE JULGAMENTO',)
                td1 = linha.find_element_by_xpath('td[1]').text
                fs = find_string(td1, chaves)
                if len(linha.find_elements_by_xpath('td[2]')) == 0 and not fs:
                    continue

                # td1 = linha.find_element_by_xpath('td[1]').text
                # td2 = linha.find_element_by_xpath('td[2]').text if len(linha.find_elements_by_xpath('td[2]')) > 0 else ''
                # print(td1, td2)
                if fs or len(movimento) == x:
                    # print('novo')
                    novo = True
                    if acp_cadastro is not None:
                        if acp_esp.strip() == '':
                            acp_esp = acp_tipo
                        else:
                            acp_esp = acp_esp.replace('Ver íntegra do(a) Despacho', '').replace('  ', ' ')
                        esp_site = corta_string(acp_esp)
                        i += 1
                        capturar = True
                        for l in lista:
                            esp_base = corta_string(l['acp_esp'])
                            if acp_cadastro == l[
                                'acp_cadastro'] and esp_site.upper().strip() == esp_base.upper().strip():
                                capturar = False
                                break

                        if not capturar and not completo and i >= 10:
                            break

                        acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp.strip(), 'acp_tipo': acp_tipo}

                        if capturar:
                            movs.append(acp)

                        self.movs.append({**acp, 'novo': capturar})

                    if find_string(td1, chaves[3:]) or len(movimento) == x:
                        break

                    if len(linha.find_elements_by_xpath('td[2]')) == 0:
                        continue

                    acp_cadastro = None
                    acp_tipo = linha.find_element_by_xpath('td[2]').text
                    acp_esp = ''

                    continue

                if novo:
                    try:
                        acp_cadastro = linha.find_element_by_xpath('td[2]').text
                        if self.grau == 1:
                            acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y')
                        else:
                            acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y %H:%M')
                        novo = False
                    except:
                        acp_esp += linha.find_element_by_xpath('td[1]').text + ' ' + linha.find_element_by_xpath(
                            'td[2]').text + ' '
                    continue

                td1 = linha.find_element_by_xpath('td[1]').text.strip()
                if td1 == '':
                    continue
                td2 = linha.find_element_by_xpath('td[2]').text.strip()
                acp_esp += td1 + ' ' + td2 + ' '

        return movs

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

        check = False

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
