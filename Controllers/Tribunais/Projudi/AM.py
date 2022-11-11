from Controllers.Tribunais.Projudi._projudi import *


# CLASSE DA VARREDURA DO PROJUDI DO AM. HERDA OS METODOS DA CLASSE PROJUDI
class AM(Projudi):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://projudi.tjam.jus.br/projudi/usuario/logon.do?actionType=inicio&r"
        self.pagina_busca = "https://projudi.tjam.jus.br/projudi/processo/buscaProcessosQualquerInstancia.do?actionType=iniciar"
        self.diferenciar_id_download_2g = True
