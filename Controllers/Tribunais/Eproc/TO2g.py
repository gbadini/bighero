from Controllers.Tribunais.Eproc._eproc2g import *


# CLASSE DA VARREDURA DO EPROC DO TO DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE EPROC2g
class TO2g(Eproc2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://eproc1.tjto.jus.br/eprocV2_prod_1grau/"
        # self.pagina_inicial_1g = "https://eproc1.tjto.jus.br/eprocV2_prod_1grau/"
        self.pagina_inicial_2g = "https://eproc2.tjto.jus.br/eprocV2_prod_2grau/"
        self.intervalo = 15
        self.ordem_usuario = 0
        self.reiniciar_navegador = False