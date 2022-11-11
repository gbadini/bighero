from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
Base = declarative_base()

# MONTA TABELA "PROCESSO_PENDENCIA"
class ProcessoPendenciaTable(Base):
    __tablename__ = "processo_pendencia"
    prp_id = Column(BIGINT, primary_key=True, autoincrement=True)
    prp_prc_id = Column(BIGINT)
    prp_tipo = Column(VARCHAR(150))
    prp_responsavel = Column(VARCHAR(150))
    prp_data = Column(DATETIME)
    prp_serventia = Column(VARCHAR(150))
    prp_status = Column(VARCHAR(150))
    prp_tabela = Column(VARCHAR(50))
    prp_plataforma = Column(INTEGER)

class ProcessoPendencia():
    # INSERE AUDIÊNCIAS
    @staticmethod
    def insert(base, prc_id, plataforma, audiencias):
        '''
        :param Session base: conexão de destino
        :param int prc_id: id do processo
        :param int plataforma: id do processo
        :param list audiencias: lista de acompanhamentos
        '''
        if len(audiencias) == 0:
            return

        s = select([ProcessoPendenciaTable]).where(column("prp_prc_id") == prc_id).where(or_(column("prp_plataforma") == plataforma, column("prp_plataforma") == None))
        result = base.execute(s)
        result = result.fetchdict()

        auds = {}
        for aud in audiencias:
            aud['prp_plataforma'] = plataforma
            prp_data = aud['prp_data'].strftime('%Y-%m-%d %H:%M')
            if 'prp_serventia' in aud and aud['prp_serventia'] is not None:
                aud['prp_serventia'] = corta_string(aud['prp_serventia'], 150)

            if prp_data not in auds:
                auds[prp_data] = aud
            else:
                if auds[prp_data]['data_mov'] < aud['data_mov']:
                    auds[prp_data] = aud

        aud_insert = []
        aud_update = []
        for aud in auds.copy():
            for r in result[:]:
                if r['prp_data'] == auds[aud]['prp_data']:
                    if r['prp_tipo'] != auds[aud]['prp_tipo'] or r['prp_status'] != auds[aud]['prp_status'] \
                            or ('prp_serventia' in auds[aud] and r['prp_serventia'] != auds[aud]['prp_serventia']):
                        del auds[aud]['data_mov']
                        auds[aud]['prp_id'] = r['prp_id']
                        aud_update.append(auds[aud])
                    result.remove(r)
                    del auds[aud]
                    break

        for aud in auds:
            del auds[aud]['data_mov']
            auds[aud]['prp_prc_id'] = prc_id
            auds[aud]['prp_tabela'] = 'Audiência'
            aud_insert.append(auds[aud])

        if len(aud_insert) > 0:
            base.execute(
                ProcessoPendenciaTable.__table__.insert(),
                aud_insert
            )
            base.commit()

        for aud in aud_update:
            prp_id = aud['prp_id']
            del aud['prp_id']
            upd = ProcessoPendenciaTable.__table__.update().values(aud). \
                where(column("prp_id") == prp_id)
            base.execute(upd)
            base.commit()