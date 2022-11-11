from Controllers.Tribunais.Esaj._esaj import *


# CLASSE DA VARREDURA DO ESAJ DO AM. HERDA OS METODOS DA CLASSE ESAJ
class AM(Esaj):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://consultasaj.tjam.jus.br/sajcas/login?service=https%3A%2F%2Fconsultasaj.tjam.jus.br%2Fesaj%2Fj_spring_cas_security_check"
        self.pagina_busca = "https://consultasaj.tjam.jus.br/cpopg/open.do"
        self.pagina_processo = "https://consultasaj.tjam.jus.br/cpopg/show.do?processo.codigo="
        self.intervalo = 8