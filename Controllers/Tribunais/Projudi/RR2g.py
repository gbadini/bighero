from Controllers.Tribunais.Projudi._projudi2g import *

# CLASSE DA VARREDURA DO PJE DE RO DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE PJE
class RR2g(Projudi2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://projudi.tjrr.jus.br/projudi/usuario/logon.do?actionType=inicio&r="
        self.pagina_busca = "https://projudi.tjrr.jus.br/projudi/processo/buscaProcessosQualquerInstancia.do?actionType=iniciar"
        self.diferenciar_id_download_2g = True
        self.kill_nao_localizado = True