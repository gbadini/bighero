from Controllers.Tribunais.Trt._trt2g_v2 import *

# CLASSE DA VARREDURA DO PJE DO TRT. HERDA OS METODOS DA CLASSE TRT
class TRT172g(Trt2g_v2):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.trt17.jus.br/segundograu/login.seam"
        self.pagina_busca = "https://pje.trt17.jus.br/segundograu/Painel/painel_usuario/advogado.seam"