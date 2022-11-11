from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
from Models.processoParteModel import *
Base = declarative_base()

# MONTA TABELA "PARTE"
class ParteTable(Base):
    __tablename__ = "parte"
    prt_id = Column(BIGINT, primary_key=True, autoincrement=True)
    prt_nome = Column(VARCHAR(150))
    prt_cpf_cnpj = Column(VARCHAR(20))


class Parte():
    # CONFERE E INSERE PARTES
    @staticmethod
    def insert(base, prc_id, partes, plataforma, apagar_partes_inexistentes):
        '''
        :param Session base: conexão de destino
        :param int prc_id: id do processo
        :param dict partes: lista de partes
        '''
        if len(partes['ativo']) == 0 and len(partes['passivo']) == 0:
            return

        for polo in partes:
            docs = []
            for prt in partes[polo]:
                prt['prt_cpf_cnpj'] = prt['prt_cpf_cnpj'].replace('.', '').replace('/', '').replace('\\', '').replace('-', '').strip()

                if prt['prt_cpf_cnpj'] is None or prt['prt_cpf_cnpj'].upper() == 'NÃO CADASTRADO' or prt['prt_cpf_cnpj'].strip() == '':
                    prt['prt_cpf_cnpj'] = 'Não Informado'
                if prt['prt_cpf_cnpj'].strip('0') == '':
                    prt['prt_cpf_cnpj'] = 'Não Informado'

                if prt['prt_cpf_cnpj'].upper() != 'NÃO INFORMADO':
                    if prt['prt_cpf_cnpj'] not in docs:
                        docs.append(prt['prt_cpf_cnpj'])
                    else:
                        prt['prt_cpf_cnpj'] = 'Delete'

                prt['prt_nome'] = prt['prt_nome'].upper().replace('(EM RECUPERAÇÃO JUDICIAL)','').replace("'","")
                prt['prt_nome'] = strip_html_tags(prt['prt_nome'])
                prt['prt_nome'] = prt['prt_nome'].capitalize()
                prt['prt_nome'] = corta_string(prt['prt_nome'], 150)
                prt['prt_nome'] = prt['prt_nome'].replace('  ',' ').strip()

                if prt['prt_cpf_cnpj'].upper() == 'NÃO INFORMADO':
                    tmp = prt['prt_nome'].upper().replace('Ô', 'O')
                    if tmp.find('VIVO') > -1 and tmp.find('TELEFONICA DO BRASIL') > -1 and len(tmp) <= 32:
                        prt['prt_nome'] = 'VIVO - TELEFÔNICA BRASIL S.A.'

                    if tmp.find('VIVO') > -1 and tmp.find('TELEFONICA BRASIL') > -1 and len(tmp) <= 30:
                        prt['prt_nome'] = 'VIVO - TELEFÔNICA BRASIL S.A.'

                    if tmp.find('VIVO') > -1 and tmp.find('TELEFONIA BRASIL') > -1 and len(tmp) <= 30:
                        prt['prt_nome'] = 'VIVO TELEFONIA BRASIL S.A.'

                    if tmp.find('TELEFONICA DO BRASIL') > -1 and len(tmp) <= 25:
                        prt['prt_nome'] = 'TELEFÔNICA BRASIL S.A.'

                    if tmp.find('TELEFONICA BRASIL') > -1 and len(tmp) <= 23:
                        prt['prt_nome'] = 'TELEFÔNICA BRASIL S.A.'

                    if (tmp.find('VIVO S') > -1 or tmp.find('VIVO/S') > -1) and len(tmp) <= 10:
                        prt['prt_nome'] = 'VIVO S.A.'

                    if find_string(tmp, ('COMPANHIA DE ELETRICIDADE DA BAHIA','CIA DE ELETRICIDADE DO ESTADO','CIA ELÉTRICA DO ESTADO','COMPANHIA DE ELETRICIDADE DO ESTADO','COMPANHIA ELÉTRICA DO ESTADO')) and tmp.find('COELBA') > -1 and len(tmp) < 55:
                        prt['prt_nome'] = 'COELBA - COMPANHIA DE ELETRICIDADE DO ESTADO DA BAHIA'

                    if tmp.find('COELBA') > -1 and len(tmp) < 12:
                        prt['prt_nome'] = 'COELBA - COMPANHIA DE ELETRICIDADE DO ESTADO DA BAHIA'

        ppt = []
        docs = []
        nomes = []
        # FORMATA CPFS PARA QUERY
        for t in partes:
            for p in partes[t][:]:
                if p['prt_cpf_cnpj'] == 'Delete':
                    partes[t].remove(p)
                    continue

                if p['prt_cpf_cnpj'].upper() != 'NÃO INFORMADO':
                    docs.append(p['prt_cpf_cnpj'])
                else:
                    nomes.append(p['prt_nome'])

        query_and = ""
        if len(nomes) > 0:
            query_and = "(prt_cpf_cnpj = 'Não Informado' and prt_nome in ('"+"','".join(nomes)+"'))"

        if len(docs) > 0:
            if query_and != '':
                query_and += " OR "
            query_and += " prt_cpf_cnpj IN ('"+"','".join(docs)+"')"

        query = "SELECT prt_id,prt_nome,prt_cpf_cnpj,ppt_id,ppt_polo,ppt_plt_id FROM parte "\
                "LEFT JOIN processo_parte on prt_id=ppt_prt_id and ppt_prc_id="+str(prc_id)+" and (ppt_plt_id = "+str(plataforma)+" or ppt_plt_id is null)"\
                "WHERE ppt_id is not null or ("+query_and+") order by ppt_polo"
        # print(query)
        result = base.execute(query)
        result = result.fetchdict()

        # ELIMINA DUPLICATAS
        new_result = []
        ids = []
        for r in result:
            incluir = True
            for n in new_result:
                if r['prt_nome'].strip().upper() == n['prt_nome'].strip().upper():
                    if n['prt_cpf_cnpj'] == r['prt_cpf_cnpj'] and n['ppt_polo'] == r['ppt_polo']:
                        if r['ppt_plt_id'] is not None and r['ppt_id'] is not None and r['ppt_plt_id'] == plataforma:
                            ids.append(r['ppt_id'])

                        incluir = False
                        continue

                # if r['prt_nome'].upper() == n['prt_nome'].upper() or (r['prt_cpf_cnpj'] == n['prt_cpf_cnpj'] and r['prt_cpf_cnpj'] != 'Não Informado'):
                #     if n['ppt_id'] is None and r['ppt_id'] is not None:
                #         n['ppt_id'] = r['ppt_id']
                #         n['ppt_polo'] = r['ppt_polo']

                    incluir = True
                    break

            if incluir:
                new_result.append(r)

        # CONFERE QUAIS ITENS JÁ EXISTEM NA TABELA PARTES E QUAIS JÁ ESTÃO VINCULADOS NA TABELA PROCESSO_PARTE
        result = new_result[:]
        for t in partes:
            for index, p in enumerate(partes[t][:]):
                ppt_id, prt_id, result = Parte.compara_itens(p, result, t)
                if ppt_id is not None:
                    continue

                if prt_id is None:
                    prt_id = base.execute(ParteTable.__table__.insert(), partes[t][index]).inserted_primary_key[0]
                    base.commit()

                ppt.append({'ppt_polo': t, 'ppt_prt_id': prt_id, 'ppt_prc_id': prc_id, 'ppt_plt_id': plataforma})

        # ids = []
        for r in result:
            if r['ppt_id'] is not None:
                ids.append(r['ppt_id'])

        if apagar_partes_inexistentes:
            if len(ids) > 0:
                ProcessoParte.delete(base, ids)

        if len(ppt) > 0:
            ProcessoParte.insert(base, ppt)

    # CONFERE SE ELEMENTO EXISTE NA BASE E SE ESTÁ VINCULADO AO PROCESSO, SE JÁ EXISTIR E ESTIVER VINCULADO, ELIMINA O ITEM
    @staticmethod
    def compara_itens(tj, db, polo):
        prt_id = None
        ppt_id = None
        fc = []
        for r in db:
            if (tj['prt_cpf_cnpj'] == r['prt_cpf_cnpj'] and r['prt_cpf_cnpj'].upper() != 'NÃO INFORMADO') or (tj['prt_nome'].upper() == r['prt_nome'].upper() and r['prt_cpf_cnpj'].upper() == 'NÃO INFORMADO'):
                fc.append(r)

        remover = None
        for r in fc:
            if prt_id is None or r['prt_cpf_cnpj'].upper() != 'NÃO INFORMADO':
                prt_id = r['prt_id']

            if remover is None or r['prt_cpf_cnpj'].upper() != 'NÃO INFORMADO' and r['ppt_id'] is not None:
                if (r['ppt_polo'] is None and r['prt_cpf_cnpj'].upper() != 'NÃO INFORMADO') or (r['ppt_polo'] is not None and r['ppt_polo'].upper().find(polo.upper()) > -1):
                    ppt_id = r['ppt_id']
                    remover = r

        if remover is not None:
            db.remove(remover)


        return ppt_id, prt_id, db