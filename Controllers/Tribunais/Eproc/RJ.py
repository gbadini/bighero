from Controllers.Tribunais.Eproc._eproc import *


# CLASSE DA VARREDURA DO EPROC DO RJ. HERDA OS METODOS DA CLASSE EPROC
class RJ(Eproc):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://eproc.jfrj.jus.br/eproc/externo_controlador.php?acao=principal&sigla_orgao_sistema=TRF2&sigla_sistema=Eproc"
        self.intervalo = 7
