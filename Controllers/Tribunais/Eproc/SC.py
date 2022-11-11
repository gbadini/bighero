from Controllers.Tribunais.Eproc._eproc import *


# CLASSE DA VARREDURA DO EPROC DE SC. HERDA OS METODOS DA CLASSE EPROC
class SC(Eproc):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://eproc1g.tjsc.jus.br/eproc/externo_controlador.php?acao=principal&sigla_orgao_sistema=TJSC&sigla_sistema=Eproc"
        self.intervalo = 7