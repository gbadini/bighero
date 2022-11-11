from Controllers.Tribunais.Esaj._esaj2g import *

# CLASSE DA VARREDURA DO ESAJ DO AM DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE ESAJ2g
class AM2g(Esaj2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://consultasaj.tjam.jus.br/sajcas/login?service=https%3A%2F%2Fconsultasaj.tjam.jus.br%2Fesaj%2Fj_spring_cas_security_check"
        self.pagina_busca = "https://consultasaj.tjam.jus.br/cposgcr"
        self.pagina_processo = "https://consultasaj.tjam.jus.br/cposgcr/show.do?localPesquisa.cdLocal=900&processo.codigo="
