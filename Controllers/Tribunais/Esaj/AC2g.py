from Controllers.Tribunais.Esaj._esaj2g import *

# CLASSE DA VARREDURA DO ESAJ DO AC DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE ESAJ2g
class AC2g(Esaj2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://esaj.tjac.jus.br/sajcas/login?service=https%3A%2F%2Fesaj.tjac.jus.br%2Fesaj%2Fj_spring_cas_security_check"
        self.pagina_busca = "https://esaj.tjac.jus.br/cposg5"
        self.pagina_processo = "https://esaj.tjac.jus.br/cposg5/show.do?processo.codigo="

