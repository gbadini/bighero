from Controllers.Tribunais.Esaj._esaj2g import *

# CLASSE DA VARREDURA DO ESAJ DE SC DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE ESAJ2g
class SP2g(Esaj2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://esaj.tjsp.jus.br/sajcas/login?service=https%3A%2F%2Fesaj.tjsp.jus.br%2Fesaj%2Fj_spring_cas_security_check"
        self.pagina_busca = "https://esaj.tjsp.jus.br/cposg/open.do"
        self.pagina_processo = "https://esaj.tjsp.jus.br/cposg/show.do?processo.codigo="

