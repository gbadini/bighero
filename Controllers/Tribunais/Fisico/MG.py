from Controllers.Tribunais.Fisico._fisico import *
import urllib.parse as urlparse
from urllib.parse import parse_qs

# CLASSE DA VARREDURA DO FÍSCO DO MG. HERDA OS METODOS DA CLASSE PROJUDIV2
class MG(Fisico):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "chrome://version/"
        self.pagina_busca = "https://www.tjmg.jus.br/portal-tjmg/processos/andamento-processual"
        # self.pagina_processo = "https://www4.tjmg.jus.br/juridico/sf/proc_resultado.jsp?tipoPesquisa=1&nomePessoa=&tipoPessoa=X&naturezaProcesso=0&situacaoParte=X&codigoOAB=&tipoOAB=N&ufOAB=MG&numero=1&select=1&tipoConsulta=1&natureza=0&ativoBaixado=X&https://www4.tjmg.jus.br/juridico/sf/proc_resultado.jsp?tipoPesquisa=1&nomePessoa=&tipoPessoa=X&naturezaProcesso=0&situacaoParte=X&codigoOAB=&tipoOAB=N&ufOAB=MG&numero=1&select=1&tipoConsulta=1&natureza=0&ativoBaixado=X&https://www4.tjmg.jus.br/juridico/sf/proc_resultado.jsp?tipoPesquisa=1&nomePessoa=&tipoPessoa=X&naturezaProcesso=0&situacaoParte=X&codigoOAB=&tipoOAB=N&ufOAB=MG&numero=1&select=1&tipoConsulta=1&natureza=0&ativoBaixado=X&listaProcessos="

    # CONFERE SE O CÓDIGO É VALIDO
    def check_codigo(self, codigo):
        '''
        :param str codigo: codigo _GET de acesso
        '''
        if codigo is None:
            return False

        if codigo.strip() == '':
            return False

        if codigo.find('txtProcesso') == -1:
            return False

        return True

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc):
        adc = self.audiencias()
        prt = self.partes()
        adv = self.responsaveis()
        status_atual = 'Ativo' if self.completo else proc['prc_status']
        prc = self.dados(status_atual)

        return adc, prt, prc, adv

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        self.driver.find_element_by_id('txtProcesso').clear()
        self.driver.find_element_by_id('txtProcesso').send_keys(numero_busca)
        self.driver.find_element_by_id('txtProcesso').send_keys(Keys.ENTER)

        if aguarda_alerta(self.driver, 1):
            return False

        msg_erro = self.driver.find_element_by_xpath('/html/body/p[5]/strong')
        if msg_erro:
            if msg_erro.text.find('Nenhum processo') > -1:
                return False

        msg_erro = self.driver.find_element_by_xpath('/html/body/h1')
        if msg_erro:
            if msg_erro.text.find('Selecionar comarca') > -1:
                return False

        return True

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        aguarda_presenca_elemento(self.driver, '/html/body/table[2]/tbody/tr[1]/td/b')
        el = self.driver.find_element_by_xpath('/html/body/table[2]/tbody/tr[1]/td/b')
        numero_site = ''
        if el:
            cnj = localiza_cnj(el.text)
            numero_site = ajusta_numero(cnj)
            if numero_busca == numero_site:
                return True

        raise MildException("Número CNJ Diferente - "+numero_site+" "+numero_busca, self.uf, self.plataforma, self.prc_id)

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self, ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        acp_esp = self.driver.find_element_by_id('descricaoProc1_0').text.strip()
        acp_cad = self.driver.find_element_by_id('dataProc1_0').text.strip()
        data_cad = datetime.strptime(acp_cad, '%d/%m/%Y')
        return Acompanhamento.compara_mov(base, prc_id, acp_esp, data_cad, self.plataforma, self.grau, rec_id=self.rec_id)

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
        rec_id = proc_data['rec_id'] if 'rec_id' in proc_data else None

        # self.driver.find_element_by_xpath('/html/body/table[7]/tbody/tr/td[2]/b/a').click()
        self.driver.find_element_by_partial_link_text('Todos Andamentos').click()

        self.movs = []
        movs = []

        movimentos = self.driver.find_elements_by_xpath('/html/body/table[2]/tbody/tr')

        # BUSCA MOVIMENTAÇÕES DO PROCESSO NA BASE
        lista = Acompanhamento.lista_movs(base, prc_id, self.plataforma, acp_grau=self.grau, rec_id=rec_id)

        i = 0
        for mov in movimentos:
            i += 1
            td_cadastro = str(4) if self.grau == 1 else str(3)
            td_usuario = str(3) if self.grau == 1 else str(4)
            acp_cadastro = mov.find_elements_by_xpath('td['+td_cadastro+']')

            if len(acp_cadastro) == 0:
                continue

            acp_cadastro = acp_cadastro[0].text.strip()
            if len(acp_cadastro) < 12:
                acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y')
            else:
                acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y %H:%M')

            acp_tipo = ''
            acp_esp = mov.find_element_by_xpath('td[2]').text.strip()
            acp_usuario = mov.find_element_by_xpath('td['+td_usuario+']').text.strip()
            if self.grau == 2:
                acp_tipo = acp_esp
                acp_esp = acp_usuario
                acp_esp = acp_tipo if acp_esp == '' else acp_esp

            capturar = True
            esp_site = corta_string(acp_esp)
            for l in lista:
                esp_base = corta_string(l['acp_esp'])
                if acp_cadastro == l['acp_cadastro'] and esp_site.strip() == esp_base.strip():
                    capturar = False
                    break

            if not capturar and not completo and i >= 10:
                break

            if self.grau == 1:
                acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp, 'acp_usuario': acp_usuario, 'acp_tipo': acp_tipo}
            else:
                acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp, 'acp_tipo': acp_tipo}

            if capturar:
                movs.append(acp)

            self.movs.append({**acp, 'novo': capturar})

        if len(self.movs) == 0:
            raise MildException("Erro ao capturar Movs", self.uf, self.plataforma, self.prc_id)

        self.driver.execute_script("history.back(); return false")
        return movs

    # CAPTURA AUDIENCIAS DO PROCESSO
    def audiencias(self):
        adcs = []
        for mov in self.movs:
            if not self.completo and not mov['novo']:
                break

            esp = mov['acp_esp'].upper().strip()
            esp = esp.replace('Ê','E')

            f = esp.find('AUDIENCIA')
            if f != 0:
                continue
            acp_cadastro = mov['acp_cadastro'].strftime('%d/%m/%Y')
            aud_txt = mov['acp_esp'].upper().strip()+" "+acp_cadastro+" "+mov['acp_usuario'].upper().strip()

            aud = localiza_audiencia(aud_txt, formato_re='(\\d+)(\\/)(\\d+)(\\/)(\\d+)(\\s+)(\\d+)(\\:)(\\d+)')
            if not aud:
                continue

            if 'prp_status' not in aud:
                aud['prp_status'] = 'Designada'

            if 'prp_tipo' not in aud:
                raise MildException("Audiência - Tipo não localizado: "+esp, self.uf, self.plataforma, self.prc_id)

            aud['data_mov'] = mov['acp_cadastro']
            adcs.append(aud)

        return adcs

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        self.driver.find_element_by_partial_link_text('Todas as Partes/Advogados').click()

        partes = {'ativo': [], 'passivo': [], 'terceiro': []}
        ultimo_polo = ''
        tb = self.driver.find_elements_by_xpath('/html/body/table[2]/tbody/tr')
        for tr in tb:
            td1 = tr.find_element_by_xpath('td[1]').text.strip()

            polo = ''
            if find_string(td1,self.titulo_partes['ignorar']):
                continue

            if find_string(td1,self.titulo_partes['ativo']):
                polo = 'ativo'
            if find_string(td1,self.titulo_partes['passivo']):
                polo = 'passivo'
            if find_string(td1,self.titulo_partes['terceiro']):
                polo = 'terceiro'

            if td1 == '' and ultimo_polo != '':
                polo = ultimo_polo

            if polo == '':
                raise MildException("polo vazio "+td1, self.uf, self.plataforma, self.prc_id)

            prt_nomes = tr.find_element_by_xpath('td[2]').get_attribute('innerHTML')
            cnt = prt_nomes.split('<table')
            prt_nome = cnt[0]
            f = prt_nome.find(f'\n')
            if f > -1:
                prt_nome = prt_nome[:f]

            partes[polo].append({'prt_nome': prt_nome, 'prt_cpf_cnpj': 'Não Informado'})
            ultimo_polo = polo


        return partes

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []

        tb = self.driver.find_elements_by_xpath('/html/body/table[2]/tbody/tr')
        ultimo_polo = ''
        for tr in tb:
            td1 = tr.find_element_by_xpath('td[1]').text
            polo = ''
            if find_string(td1, self.titulo_partes['ignorar']):
                continue

            if find_string(td1, self.titulo_partes['ativo']):
                polo = 'Polo Ativo'
            if find_string(td1, self.titulo_partes['passivo']):
                polo = 'Polo Passivo'

            if td1 == '' and ultimo_polo != '':
                polo = ultimo_polo

            advs = tr.find_elements_by_xpath('td[2]/table/tbody/tr/td[2]/table/tbody/tr')
            for adv in advs:
                prr_nome = adv.find_element_by_xpath('td[2]').text
                prr_oab = adv.find_element_by_xpath('td[1]').text
                resps.append({'prr_nome': prr_nome[2:].strip(), 'prr_oab': prr_oab.strip(), 'prr_cargo': 'Advogado', 'prr_parte': polo})
                ultimo_polo = polo

        self.driver.execute_script("history.back(); return false")

        if self.grau == 1:
            trs = self.driver.find_elements_by_xpath('/html/body/table[2]/tbody/tr')
            achei = False
            for tr in trs:
                tds = tr.find_elements_by_tag_name('td')
                if len(tds) > 5:
                    continue

                for td in tds:
                    titulo = td.find_element_by_tag_name('b').text
                    if titulo.upper().find('JUIZ(IZA)') > -1:
                        html = td.get_attribute('innerHTML')
                        cnt = html.split('</b>')
                        prr_nome = cnt[1].strip()
                        prr_nome = strip_html_tags(prr_nome)
                        resps.append({'prr_nome': prr_nome.strip(), 'prr_oab': '', 'prr_cargo': 'Juiz', 'prr_parte': ''})
                        achei = True
                        break

                if achei:
                    break


        return resps

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        '''
        :param str status_atual: Status atual
        '''
        prc = {}

        url = self.driver.execute_script('return window.location')
        parsed = urlparse.urlparse(url['href'])
        parse_qs(parsed.query)
        url_params = parse_qs(parsed.query)
        prc['prc_codigo'] = url_params['listaProcessos'][0]+'&txtProcesso='+url_params['txtProcesso'][0]+'&comrCodigo='+url_params['comrCodigo'][0]

        prc_comarca2 = self.driver.find_element_by_xpath('/html/body/table[2]/tbody/tr[1]/td/b').text
        prc['prc_numero2'] = localiza_cnj(prc_comarca2)

        self.driver.find_element_by_xpath('/html/body/table[7]/tbody/tr/td[1]/b/a').click()

        # LOCALIZA STATUS DO PROCESSO
        prc['prc_status'] = get_status(self.movs, status_atual)

        campos = {'Valor da causa': 'prc_valor_causa', 'Classe': 'prc_classe', 'Assunto': 'prc_assunto', 'Distribuição': 'prc_distribuicao' }
        trs = self.driver.find_elements_by_xpath('/html/body/table[2]/tbody/tr')
        for tr in trs:
            tds = tr.find_elements_by_tag_name('td')
            if len(tds) > 5:
                continue

            for td in tds:
                titulo = td.find_element_by_tag_name('b').text
                for c in campos:
                    if titulo.upper().find(c.upper()) > -1:
                        html = td.get_attribute('innerHTML')
                        cnt = html.split('</b>')
                        texto = cnt[1]
                        texto = strip_html_tags(texto)
                        prc[campos[c]] = texto.strip()
                        break


        prc_serventia = self.driver.find_elements_by_xpath('/html/body/h1')
        if len(prc_serventia) == 0:
            raise MildException("Erro na captura de dados", self.uf, self.plataforma, self.prc_id)

        prc_serventia = prc_serventia[0].text
        f = prc_serventia.find('-')
        prc_serventia = prc_serventia[:f].strip()
        prc['prc_serventia'] = prc_serventia
        prc['prc_juizo'] = prc_serventia
        prc['prc_comarca2'] = localiza_comarca(prc_serventia, self.uf)

        if 'prc_distribuicao' in prc:
            r = re.search('(\\d+)(\\/)(\\d+)(\\/)(\\d+)', prc['prc_distribuicao'])
            prc_distribuicao = r.group(0)
            prc['prc_distribuicao'] = datetime.strptime(prc_distribuicao, '%d/%m/%Y')

        return prc