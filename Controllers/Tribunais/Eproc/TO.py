from Controllers.Tribunais.Eproc._eproc import *


# CLASSE DA VARREDURA DO EPROC DO TO. HERDA OS METODOS DA CLASSE EPROC
class TO(Eproc):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://eproc1.tjto.jus.br/eprocV2_prod_1grau/"
        self.intervalo = 10
        self.ordem_usuario = 0
        self.reiniciar_navegador = False