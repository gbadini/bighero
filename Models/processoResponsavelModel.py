from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
Base = declarative_base()

# MONTA TABELA "PROCESSO_RESPONSAVEL"
class ProcessoResponsavelTable(Base):
    __tablename__ = "processo_responsavel"
    prr_id = Column(BIGINT, primary_key=True, autoincrement=True)
    prr_prc_id = Column(BIGINT)
    prr_nome = Column(VARCHAR(100))
    prr_cargo = Column(VARCHAR(100))
    prr_oab = Column(VARCHAR(45))
    prr_parte = Column(VARCHAR(250))
    prr_plt_id = Column(INTEGER)

class ProcessoResponsavel():
    # INSERE ADVOGADOS/JUIZ
    @staticmethod
    def insert(base, prc_id, responsaveis, plataforma, apagar_partes_inexistentes):
        '''
        :param Session base: conexão de destino
        :param int prc_id: id do processo
        :param list responsaveis: lista de acompanhamentos
        '''
        if len(responsaveis) == 0:
            return

        nomes = []
        for rsp in responsaveis[:]:
            if find_string(rsp['prr_nome'], ('Advogado não cadastrado','Sem Advogado Constituído','sem advogado nos autos','SEM INFORMACAO ADVOGADO',)):
                responsaveis.remove(rsp)
                continue

            rsp['prr_nome'] = rsp['prr_nome'].replace('  ',' ').replace('(ADVOGADO)',' ').replace('(ADVOGADA)','')\
                .replace('(ADVOGADO(A))','').replace('Advogada:','').replace('Advogado:','').strip()
            if rsp['prr_nome'] in nomes:
                responsaveis.remove(rsp)
            else:
                nomes.append(rsp['prr_nome'])

        s = select([ProcessoResponsavelTable]).where(column("prr_prc_id") == prc_id).where(or_(column("prr_plt_id") == plataforma, column("prr_plt_id") == None))
        result = base.execute(s)
        result = result.fetchdict()

        for rsp in responsaveis[:]:
            achei = False
            for r in result[:]:
                if rsp['prr_nome'] == r['prr_nome'] and rsp['prr_parte'] == r['prr_parte']:
                    responsaveis.remove(rsp)
                    result.remove(r)
                    achei = True
                    break

            rsp['prr_plt_id'] = plataforma
            if not achei:
                rsp['prr_prc_id'] = prc_id


        if apagar_partes_inexistentes:
            ids = []
            if len(result)>0:
                for r in result:
                    ids.append(r['prr_id'])

                ProcessoResponsavel.delete(base, ids)

        if len(responsaveis) > 0:
            base.execute(
                ProcessoResponsavelTable.__table__.insert(),
                responsaveis
            )
            base.commit()


    # APAGA ADVOGADOS/JUIZ
    @staticmethod
    def delete(base, ids):
        '''
        :param Session base: conexão de destino
        :param list ids: lista de ids que será apagados
        '''
        delete_q = ProcessoResponsavelTable.__table__.delete().where(ProcessoResponsavelTable.prr_id.in_(ids))
        base.execute(delete_q)
        base.commit()