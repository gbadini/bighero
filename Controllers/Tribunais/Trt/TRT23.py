from Controllers.Tribunais.Trt._trt_v2 import *

# CLASSE DA VARREDURA DO PJE DO DF. HERDA OS METODOS DA CLASSE PJE
class TRT23(TrtV2):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.trt23.jus.br/primeirograu/login.seam"
        self.pagina_busca = "https://pje.trt23.jus.br/primeirograu/Painel/painel_usuario/advogado.seam"
