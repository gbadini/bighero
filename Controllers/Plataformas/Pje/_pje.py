from Controllers.Plataformas.Pje.pg import PjePg
from Controllers.Plataformas.Pje.sg import PjeSg

def Pje(versao=1, grau=1):
    versions = {1: {1: PjePg, 2: PjeSg}}
    class SpecificClass(versions[versao][grau]):
        def __init__(self, *args, **kwargs):
            super(SpecificClass, self).__init__(*args, **kwargs)
    return SpecificClass
