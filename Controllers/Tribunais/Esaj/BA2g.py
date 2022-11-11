from Controllers.Tribunais.Esaj._esaj2g import *

# CLASSE DA VARREDURA DO ESAJ DA BA DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE ESAJ2g
class BA2g(Esaj2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "http://esaj.tjba.jus.br/sajcas/login?service=http%3A//esaj.tjba.jus.br/esaj/portal.do%3Fservico%3D740000"
        self.pagina_busca = "http://esaj.tjba.jus.br/cpo/sg/search.do"
        self.pagina_processo = "http://esaj.tjba.jus.br/cpo/sg/show.do?processo.codigo="
        self.id_mensagem_erro = 'spwTabelaMensagem'