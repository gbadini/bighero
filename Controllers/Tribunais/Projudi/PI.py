from Controllers.Tribunais.Projudi._projudi_v2 import *


# CLASSE DA VARREDURA DO PROJUDI DO PI. HERDA OS METODOS DA CLASSE PROJUDIV2
class PI(ProjudiV2):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://projudi.tjpi.jus.br/projudi/"
        self.pagina_busca = "https://projudi.tjpi.jus.br/projudi/buscas/ProcessosQualquerAdvogado"
        self.pagina_processo = "https://projudi.tjpi.jus.br/projudi/listagens/DadosProcesso?numeroProcesso="
        self.xpath_menu = '//*[@id="topo"]/table/tbody/tr[2]/td/ul'
