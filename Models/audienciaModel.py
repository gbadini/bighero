from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
Base = declarative_base()
from datetime import date
from dateutil.relativedelta import relativedelta

# MONTA TABELA "ACOMPANHAMENTO"
class AudienciaTable(Base):
    __tablename__ = "audiencia"
    adc_id = Column(BIGINT, primary_key=True, autoincrement=True)
    adc_prc_id = Column(BIGINT)
    adc_data = Column(DATETIME)
    adc_responsavel = Column(INTEGER)
    adc_ativa = Column(BOOLEAN)
    adc_status = Column(VARCHAR(45))
    adc_valor_diligencia = Column(REAL)
    adc_valor_advogado = Column(REAL)
    adc_valor_preposto = Column(REAL)
    adc_obs = Column(VARCHAR(100))
    adc_tipo = Column(VARCHAR(65))
    adc_agenda = Column(BOOLEAN)
    adc_agn_executor = Column(INTEGER)
    adc_agn_data = Column(DATETIME)
    adc_data_cadastro = Column(DATETIME)
    adc_ignorar_sentenca = Column(BOOLEAN)


class Audiencia():
    # CAPTURAS AUDIENCIA DO PROCESSO
    @staticmethod
    def select(base, prc_id, somente_ativos=True):
        '''
        :param Session base: conexão de destino
        :param int prc_id: id do processo
        '''

        s = select([AudienciaTable]).where(column("adc_prc_id") == prc_id)
        if somente_ativos:
            s = s.where(column("adc_ativa") == 1)

        result = base.execute(s)
        return result.fetchdict()

    # INSERE AUDIENCIAS
    @staticmethod
    def insert(base, prc_id, dados):
        '''
        :param Session base: conexão de destino
        :param int prc_id: id do processo
        :param list dados: lista de audiencias
        '''
        if len(dados) == 0:
            return

        auds_base = Audiencia.select(base, prc_id)

        audiencias = []

        for d in dados[:]:
            achei = False
            for adc in audiencias:
                if adc['adc_data'] == d['adc_data'] and adc['adc_tipo'] == d['adc_tipo']:
                    achei = True
            if not achei:
                audiencias.append(d)
        del dados

        for aud_db in auds_base[:]:
            for adc in audiencias[:]:
                if aud_db['adc_data'] == adc['adc_data'] and aud_db['adc_tipo'] == adc['adc_tipo']:
                    auds_base.remove(aud_db)
                    audiencias.remove(adc)

        for aud_db in auds_base[:]:
            trimestre = datetime.today() + relativedelta(months=-24)
            if aud_db["adc_data"] <= trimestre or aud_db["adc_status"] is not None:
                auds_base.remove(aud_db)

            aud_db['adc_ativa'] = False

        for adc in audiencias:
            prev_mes = mes_anterior()
            adc['adc_agenda'] = False if adc['adc_data'] < prev_mes else None
            adc['adc_prc_id'] = prc_id
            adc['adc_ativa'] = True

        if len(audiencias) > 0:
            base.execute(
                AudienciaTable.__table__.insert(),
                audiencias
            )
            base.commit()

        Audiencia.update(base, auds_base)

    # ATUALIZA AUDIENCIAS
    @staticmethod
    def update(base, dados):
        '''
        :param Session base: conexão de destino
        :param int prc_id: id do processo
        :param list dados: lista de audiencias
        '''
        if len(dados) == 0:
            return

        for adc in dados:
            adc_id = adc['adc_id']
            del adc['adc_id']

            upd = AudienciaTable.__table__.update().values(adc).\
                where(column("adc_id") == adc_id)
            base.execute(upd)
            base.commit()
