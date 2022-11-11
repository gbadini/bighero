from Controllers.Tribunais.Esaj._esaj2g import *

# CLASSE DA VARREDURA DO ESAJ DO MS DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE ESAJ2g
class MS2g(Esaj2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://esaj.tjms.jus.br/sajcas/login?service=https%3A%2F%2Fesaj.tjms.jus.br%2Fesaj%2Fj_spring_cas_security_check"
        self.pagina_busca = "https://esaj.tjms.jus.br/cposg5/open.do?gateway=true"
        self.pagina_processo = "https://esaj.tjms.jus.br/cposg5/show.do?processo.codigo="

