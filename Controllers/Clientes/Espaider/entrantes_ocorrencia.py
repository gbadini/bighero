from Controllers.Clientes.Espaider.entrantes import Entrantes

# CAPTURA PROCESSOS ENTRANTES DO PROCESSUM
class EntrantesOcorrencia(Entrantes):

    def __init__(self):
        super().__init__()
        self.captura_ocorrencia = True
