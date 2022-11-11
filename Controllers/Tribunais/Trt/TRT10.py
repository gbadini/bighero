from Controllers.Tribunais.Trt._trt import *

# CLASSE DA VARREDURA DO PJE DO DF. HERDA OS METODOS DA CLASSE PJE
class TRT10(Trt):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pje.trt10.jus.br/primeirograu/login.seam"
        self.pagina_busca = "https://pje.trt10.jus.br/primeirograu/Painel/painel_usuario/advogado.seam"
