from Controllers.Tribunais.Trt._trt2g import *

# CLASSE DA VARREDURA DO PJE DO TRT. HERDA OS METODOS DA CLASSE TRT
class TRT102g(Trt2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.trt10.jus.br/segundograu/login.seam"
        self.pagina_busca = "https://pje.trt10.jus.br/segundograu/Painel/painel_usuario/advogado.seam"