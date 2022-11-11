from Controllers.Tribunais.Trt._trt import *
from Controllers.Tribunais.segundo_grau import *
import sys, time, shutil
import datetime

# CLASSE DA VARREDURA DO TRT. HERDA OS METODOS DA CLASSE PLATAFORMA
class Trt2g(SegundoGrau, Trt):

    # CONFERE SE OS RECURSOS ESTÃO NA BASE CASO EXISTA MAIS DE UM
    def confere_recursos(self, base, proc):
        recs = self.driver.find_elements_by_xpath('/html/body/div[5]/div/div/div[2]/div/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[2]/div/div[2]/div/div[2]/div[2]/table/tbody/tr/td[2]/div/div/a/span')

        if len(recs) == 1 and proc['rec_codigo'] is not None:
            return True

        if len(recs) > 1:
            recs.pop(0)

        achei = True
        for rec in recs:
            id = rec.get_attribute('id')
            f_id = id.split(':')

            rec_numero = localiza_cnj(rec.text)
            result = Recurso.select(base, proc['prc_id'], rec_numero=rec_numero, rec_codigo=f_id[1])
            if len(result) == 0:
                achei = False
                Recurso.insert(base, {'rec_prc_id': proc['prc_id'], 'rec_codigo': f_id[1], 'rec_numero': rec_numero,'rec_plt_id':self.plataforma})

        return achei

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc):
        adc = self.audiencias()
        prt = self.partes()
        adv = self.responsaveis()
        status_atual = 'Ativo' if self.completo else proc['rec_status']
        prc = self.dados(status_atual)

        return adc, prt, prc, adv

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca, codigo=None):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        xpath = '/html/body/div[5]/div/div/div[2]/div/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[2]/div/div[2]/div/div[2]/div[2]/table/tbody/tr/td[2]/div/div/a'
        aguarda_presenca_elemento(self.driver, xpath)
        recs = self.driver.find_elements_by_xpath(xpath)

        for rec in recs:
            id = rec.get_attribute('id')
            f_id = id.split(':')

            rec_numero = localiza_cnj(rec.text)
            numero_site = ajusta_numero(rec_numero)
            if numero_busca == numero_site and f_id[1] == codigo:
                self.clica_no_resultado()
                return True

        raise MildException("Número CNJ Diferente", self.uf, self.plataforma, self.prc_id)

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        # partes = {'ativo': [], 'passivo': [], 'terceiro':[]}

        # CLICA NA ABA DE AUDIENCIAS, PARA COLETAR AUDIENCIAS
        self.driver.find_element_by_id('informativoProcessoTrf_lbl').click()

        aguarda_presenca_elemento(self.driver, 'toggleDocumentos_header_label', tipo='ID')

        # PEGA OS DADOS DA TABELA POLO ATIVO
        tabela_parte_ativa = self.driver.find_element_by_id('listaPoloAtivo')
        tabela_parte_ativa = tabela_parte_ativa.text.split("\n")

        prts_ativo = self.separa_partes_importantes(tabela_parte_ativa)

        # PEGA OS DADOS DA TABELA POLO PASSIVO
        tabela_parte_passiva = self.driver.find_element_by_id('listaPoloPassivo')
        tabela_parte_passiva = tabela_parte_passiva.text.split("\n")

        prts_passiva = self.separa_partes_importantes(tabela_parte_passiva)

        terceiros = []
        tabela_terceiros = self.driver.find_element_by_id('listaPoloOutros')
        if tabela_terceiros:
            tabela_terceiros = tabela_terceiros.text.split("\n")

            terceiros = self.separa_partes_importantes(tabela_terceiros)

        prts = {'ativo': prts_ativo, 'passivo': prts_passiva, 'terceiro': terceiros}

        if prts_ativo == prts_passiva:
            return {'ativo': [{'prt_nome': 'AMBOS',}, ],}

        return prts

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        rec = {}

        if status_atual == 'Segredo de Justiça':
            status_atual = 'Ativo'

        rec['rec_status'] = get_status(self.movs, status_atual, grau=2)

        segundo_numero_processo = self.driver.find_element_by_id('processoIdentificadorDiv')
        rec['rec_numero'] = localiza_cnj(segundo_numero_processo.text)

        data_distribuicao = self.driver.find_element_by_id('dataDistribuicaoDecoration:dataDistribuicao')
        if data_distribuicao:
            data_distribuicao = data_distribuicao.text.strip()
            if data_distribuicao != '':
                rec['rec_distribuicao'] = datetime.datetime.strptime(data_distribuicao, '%d/%m/%Y')


        # COLETA VALOR DA CAUSA
        valor_causa = self.driver.find_element_by_id('valorCausaDecoration:valorCausa')
        rec['rec_valor'] = valor_causa.text.strip()

        # COLETA ORGÃO JULGADOR
        orgao_julgador = self.driver.find_element_by_id('orgaoJulgDecoration:orgaoJulg')
        rec['rec_orgao'] = orgao_julgador.text.strip()

        # COLETA RELATOR
        segundo_numero_processo = self.driver.find_element_by_id('relatorProcessoDecoration:relatorProcesso')
        rec['rec_relator'] = segundo_numero_processo.text.strip()

        rec['rec_assunto'] = self.coleta_prc_assunto()

        rec_segredo = self.driver.find_element_by_xpath('//*[@id="caracteristicaProcessoViewViewView"]/div/div[3]/table/tbody/tr/td[1]/span/div/span/div/div[2]')
        if not rec_segredo:
            rec_segredo = self.driver.find_element_by_id('segredoJusticaCletDecoration:divfieldsegredoJusticaClet')

        rec['rec_segredo'] = True if rec_segredo.text == 'SIM' else False

        return rec

