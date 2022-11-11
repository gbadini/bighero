from Controllers.Tribunais.Trt._trt_v2 import *
from Controllers.Tribunais.Trt._trt2g import *
from Controllers.Tribunais.segundo_grau import *
import sys, time, shutil
import datetime

# CLASSE DA VARREDURA DO TRT. HERDA OS METODOS DA CLASSE PLATAFORMA
class Trt2g_v2(TrtV2, Trt2g):

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        rec = {}

        campos = {'Órgão julgador:': 'rec_orgao', 'Assunto': 'rec_assunto', 'Valor': 'rec_valor', 'Distribuído': 'rec_distribuicao', 'Número do Processo': 'rec_numero', 'Relator': 'rec_relator'}
        dts = self.driver.find_elements_by_xpath('//*[@id="processo"]/div/div[1]/dl/*')
        i = 0
        conteudo = ''
        campo = ''
        for dt in dts:
            i += 1
            if dt.tag_name == 'dt':
                if campo != '':
                    rec[campo] = conteudo.strip().strip(',')
                conteudo = ''
                titulo = dt.text

                campo = ''
                for c in campos:
                    if titulo.upper().find(c.upper()) > -1:
                        campo = campos[c]
                        break

                if campo == '':
                    continue
            elif dt.tag_name == 'dd':
                conteudo += dt.text + ', '

            if i == len(dts):
                rec[campo] = conteudo.strip().strip(',')

        if len(rec) == 0:
            raise MildException("Erro ao abrir processo", self.uf, self.plataforma, self.prc_id, False)

        if 'rec_distribuicao' in rec:
            data_dist = localiza_data(rec['rec_distribuicao'])
            if not data_dist:
                del rec['rec_distribuicao']
            else:
                rec['rec_distribuicao'] = data_dist

        if status_atual == 'Segredo de Justiça':
            status_atual = 'Ativo'

        rec['rec_status'] = get_status(self.movs, status_atual, grau=2)

        if 'rec_numero' in rec:
            r = re.search("((\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+))", rec['rec_numero'], re.IGNORECASE | re.DOTALL)
            if r is not None:
                rec['rec_numero'] = r.group(0)

        self.driver.find_element_by_xpath('//*[@id="autuacao-dialogo"]/a/i').click()
        return rec