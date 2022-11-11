from Config.helpers import *
from Controllers.Tribunais.primeiro_grau import *
import sys, time, shutil


# CLASSE DA VARREDURA DE PROCESSOS FISICOS. HERDA OS METODOS DA CLASSE PLATAFORMA
class Fisico(PrimeiroGrau):

    def __init__(self):
        super().__init__()
        self.plataforma = 4
        self.movs = []

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc):
        status_atual = 'Ativo' if self.completo else proc['prc_status']
        adc = self.audiencias()
        prc = self.dados(status_atual)
        prt = self.partes()
        adv = self.responsaveis()

        return adc, prt, prc, adv

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def confere_arquivos_novos(self):
        return False