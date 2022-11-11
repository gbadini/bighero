from Controllers.Tribunais.Tucujuris._tucujuris import *


# CLASSE DA VARREDURA DO ESAJ DO AM. HERDA OS METODOS DA CLASSE ESAJ
class AP(Tucujuris):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "http://tucujuris.tjap.jus.br/tucujuris/pages/login/login.html"
        self.pagina_busca = "http://tucujuris.tjap.jus.br/tucujuris/pages/consultar-processo/consultar-processo.html"
        self.pagina_processo = "http://tucujuris.tjap.jus.br/tucujuris/pages/detalhes-processo/detalhes-processo.html?id="

