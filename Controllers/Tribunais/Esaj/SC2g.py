from Controllers.Tribunais.Esaj._esaj2g import *

# CLASSE DA VARREDURA DO ESAJ DE SC DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE ESAJ2g
class SC2g(Esaj2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://esaj.tjsc.jus.br/sajcas/login?service=https%3A%2F%2Fesaj.tjsc.jus.br%2Fesaj%2Fj_spring_cas_security_check"
        self.pagina_busca = "https://esaj.tjsc.jus.br/cposgtj/open.do"
        self.pagina_processo = "https://esaj.tjsc.jus.br/cposgtj/show.do?processo.codigo="

