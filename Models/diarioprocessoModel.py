from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
Base = declarative_base()

# MONTA TABELA "DIARIO PROCESSO"
class DiarioProcessoTable(Base):
    __tablename__ = "diario_processo"
    drp_id = Column(Integer, primary_key=True, autoincrement=True)
    drp_dro_id = Column(INTEGER)
    drp_processo = Column(NVARCHAR(60))
    drp_titulo = Column(NVARCHAR(200))
    drp_subtitulo = Column(NVARCHAR(100))
    drp_enunciado = Column(NVARCHAR(max))
    drp_conteudo = Column(NVARCHAR(max))
    drp_signo = Column(NVARCHAR(250))
    drp_pagina = Column(INTEGER)
    drp_empresa = Column(NVARCHAR(100))
    drp_prc_id = Column(INTEGER)
    drp_ordem = Column(INTEGER)
    drp_upload = Column(BOOLEAN)
    drp_acompanhamento = Column(BOOLEAN)

class DiarioProcesso():

    @staticmethod
    def vincular_by_processo(base, drp_processo, prc_id):
        while True:
            try:
                p = drp_processo.lstrip("0")
                p = p.replace('-', '').replace('.', '').replace('/', '')
                if p != '':
                    query ="""select drp_id from diario_processo dp WITH (NOLOCK) where 
                            (REPLACE(REPLACE(SUBSTRING(drp_processo, PATINDEX('%[^0]%', drp_processo + '.'), 
                            LEN(drp_processo)), '.', ''), '-', '')='""" + p + """') 
                            and (drp_prc_id is NULL or drp_prc_id=0) OPTION(QUERYTRACEON 8649)"""

                    result2 = base.execute(query)
                    result2 = result2.fetchdict()

                    if len(result2) > 0:
                        drps = []
                        for r in result2:
                            drps.append(r['drp_id'])

                        upd = DiarioProcessoTable.__table__.update().values(drp_prc_id=prc_id). \
                            where(column("drp_id").in_(drps))
                        base.execute(upd)
                        base.commit()

                break
            except Exception as e:
                tb = traceback.format_exc()
                print(tb)
                if tb.find('vínculo de comunicação') > -1 or tb.find('tempo limite de espera') > -1:
                    print('Erro no vínculo da conexão. Aguardando para tentar novamente')
                    base.rollback()
                    time.sleep(30)
                    continue
                raise Exception

    # SELECIONA TODOS OS ARQUIVOS VÁLIDOS JÁ EXISTENTES DO PROCESSO
    @staticmethod
    def select_diarios_entrantes(base, prc_id):
        query = """	select * from diario_processo dp 
                    inner join diario on dro_id=drp_dro_id
                    where drp_prc_id = """+str(prc_id)+""" 
                    order by dro_dia asc"""

        result = base.execute(query)
        result = result.fetchdict()
        return result
    
    # ATUALIZA DADOS ESPECIFICOS DOS DIARIOS
    @staticmethod
    def update_batch(base, drps, dados):
        if len(drps) == 0:
            return

        drp_ids = []
        for drp in drps:
            drp_ids.append(drp['drp_id'])
        for i in range(0, len(drp_ids), 800):
            ids_para_update = drp_ids[i:i + 800]
            upd = DiarioProcessoTable.__table__.update().values(dados). \
                where(column("drp_id").in_(ids_para_update))

            base.execute(upd)
            base.commit()

   # ATUALIZA DADOS ESPECIFICOS DOS DIARIOS
    @staticmethod
    def check_upload(base, drp_id):
        query = """	select * from diario_processo dp 
                    where drp_id = """+str(drp_id)

        result = base.execute(query)
        result = result.fetchdict()
        return result

        # ATUALIZA DADOS ESPECIFICOS DOS DIARIOS

    @staticmethod
    def get_drp_by_date(base, prc_id, dia):
        query = """	select * from diario dr
                    inner join diario_processo dp on drp_dro_id=dro_id 
                     where (drp_upload is NULL or drp_acompanhamento is NULL) and drp_prc_id = """ + str(prc_id) + """ and dro_dia = '"""+dia.strftime('%Y-%m-%d')+"""'"""

        result = base.execute(query)
        result = result.fetchdict()
        return result
