from Controllers.Tribunais.Projudi._projudi_v2 import *


# CLASSE DA VARREDURA DO PROJUDI DO ES. HERDA OS METODOS DA CLASSE PROJUDIV2
class ES(ProjudiV2):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://sistemas.tjes.jus.br/projudi"
        self.pagina_busca = "https://sistemas.tjes.jus.br/projudi/buscas/ProcessosQualquerAdvogado"
        self.pagina_processo = "https://sistemas.tjes.jus.br/projudi/listagens/DadosProcesso?numeroProcesso="
        self.xpath_menu = '//*[@id="topo"]/table/tbody/tr[2]/td/ul'
