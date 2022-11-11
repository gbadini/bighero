from Controllers.Clientes.spic import *
import json
from datetime import date
from dateutil.relativedelta import relativedelta

# CLASSE DA VARREDURA DO PROCESSUM. HERDA OS METODOS DA CLASSE PROCESSUM
class SPIC(SPICCliente):

    def __init__(self):
        super().__init__()