from tkinter import *
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter.ttk import Combobox
import threading
import multiprocessing as mp
from multiprocessing import Queue, Pipe, Array, Manager
import importlib
import traceback
from datetime import datetime, timedelta
import time, uuid
tasks = {}
from configparser import ConfigParser
import psutil
import schedule
from pathlib import Path
import json

# MONTA O CAMINHO PARA A CLASSE RESPECTIVA AO ESTADO E PLATAFORMA E CHAMA O METODO PARA INICIAR A VARREDURA
def rodar(q, uf, plataforma, grau, dia, tipo, query_and, headless, hora_atual, arquivo_morto, base, categoria):
    '''
    :param str uf: estado a ser localizado
    :param str plataforma: plataforma a ser localizada
    :param int grau: grau que será varrido
    :param int dia: data de referencia para varredura
    '''
    # completo = True
    data_varredura = get_data_varredura(hora_atual)
    modulo = getattr(importlib.import_module('Controllers.Tribunais' + plataforma.capitalize() + '.' + uf), uf)
    ''' INICIA A CLASSE RESPECTIVA '''
    # wd = modulo()

    qtd_threads = 1
    ids = modulo().intervalos(uf, plataforma, data_varredura, tipo, query_and, base, qtd_threads, arquivo_morto)
    del modulo

    if len(ids) == 0:
        return
    ''' INICIA A VARREDURA '''
    b_index = 0
    for b in ids:

        if len(ids[b]) == 0:
            id_proc = str(uuid.uuid1()) + '0' + str(b_index)
            q.put({'UF': uf, 'id_proc': id_proc, 'index': 0, 'base': b, 'plataforma': plataforma, 'controller': 'Controllers.' + plataforma.capitalize() + '.' + uf, 'args': False})
        else:
            for i in range(0, qtd_threads):
                id_proc = str(uuid.uuid1()) + str(i) + str(b_index)
                id_inicial = ids[b][i]
                id_final = ids[b][i+1]-1 if i+1 < len(ids[b]) else False
                # task = mp.Process(target=wd.ciclo, args=(data_varredura, tipo, query_and, b, categoria, headless, arquivo_morto, [id_inicial,id_final]))
                q.put({'UF': uf, 'id_proc': id_proc,'index': i, 'base': b, 'plataforma':plataforma, 'controller': 'Controllers.' + plataforma.capitalize() + '.' + uf, 'args': (data_varredura, tipo, query_and, b, categoria, headless, arquivo_morto, [id_inicial, id_final])})
                # lista.put({'UF': uf, 'index': i, 'base': b, 'controller': 'Controllers.' + plataforma.capitalize() + '.' + uf, 'args': (data_varredura, tipo, query_and, b, categoria, headless, arquivo_morto, [id_inicial, id_final])})
                # if uf not in tasks:
                #     tasks[uf] = []
                # tasks[uf].append(task)

        b_index += 1

# MONTA A INTERFACE GRÁFICA DA APLICAÇÃO
class MainApplication(tk.Frame):

    def list_listener(self, q):
        while True:
            time.sleep(2)
            qtd_threads = 1
            running = 0
            dead = []
            try:
                total_inst = self.instancias.get()
            except:
                total_inst = 5
            new_tasks = {}
            tasks_keys = list(self.new_tasklist)
            for key in tasks_keys:
                self.tasklist[key] = self.new_tasklist[key]
                del self.new_tasklist[key]

            for d in self.tasks_to_del[:]:
                if d in self.tasklist:
                    if self.tasklist[d]['task'] and self.tasklist[d]['task'] is not None:
                        if self.tasklist[d]['task'].is_alive():
                            parent_pid = self.tasklist[d]['task'].pid
                            parent = psutil.Process(parent_pid)
                            for child in parent.children(recursive=True):
                                try:
                                    child.kill()
                                except:
                                    pass

                            self.tasklist[d]['task'].terminate()

                if d in self.tasklist:
                    del self.tasklist[d]
                self.tasks_to_del.remove(d)

            for t in self.tasklist:
                if running >= total_inst:
                    break

                uf = self.tasklist[t]['UF']
                if self.tasklist[t]['task']:
                    if self.tasklist[t]['task'].is_alive():
                        running += 1
                    else:
                        if self.tasklist[t]['running']:
                            dead.append(t)
                        else:
                            if uf != '*':
                                if self.check_outras_bases(self.tasklist[t]):
                                    continue

                            if self.tasklist[t]['unico']:
                                if self.check_unico(dead, self.tasklist[t], t):
                                    dead.append(t)
                                    continue

                            self.tasklist[t]['task'].start()
                            self.tasklist[t]['running'] = True
                            try:
                                tv_values = self.treeview.item(t)['values']
                                tv_values[5] = "Varrendo"
                                self.treeview.item(t, values=tv_values)
                            except:
                                pass
                            running += 1
                    continue

                else:
                    
                    # CRIA UMA TASK ATRELADA A ENTRADA NO DICT CASO NÃO EXISTA
                    data_varredura = get_data_varredura(self.tasklist[t]['hora_atual'], self.tasklist[t]['dia'])
                    plataforma = self.tasklist[t]['plataforma']
                    tipo_mod = None
                    modulo = None
                    try:
                        if uf == '*':
                            tipo_mod = self.tasklist[t]['tipo']
                            file = tipo_mod.lower().replace(' ','_')
                            tipo_mod = tipo_mod.replace(' ','')
                            # print(file)
                            # print(tipo_mod)
                            print('Controllers.Clientes.' + plataforma + '.' + file)
                            modulo = getattr(importlib.import_module('Controllers.Clientes.' + plataforma + '.' + file), tipo_mod)
                        else:
                            uf_mod = uf if self.tasklist[t]['grau'] == 1 else uf + '2g'
                            plat_mod = plataforma.capitalize()
                            # plat_mod = 'Trf' if uf_mod.upper().find('TRF') > -1 else plataforma.capitalize()
                            if uf_mod.upper().find('TRF') > -1:
                                print('Controllers.Tribunais.Trf.' + uf_mod.upper() + '.' + plat_mod)
                                modulo = getattr(importlib.import_module('Controllers.Tribunais.Trf.' + uf_mod.upper() + '.' + plat_mod), plat_mod+'_'+uf_mod)
                            else:
                                print('Controllers.Tribunais.' + plat_mod + '.' + uf_mod)
                                modulo = getattr(importlib.import_module('Controllers.Tribunais.' + plat_mod + '.' + uf_mod), uf_mod)

                    except:
                        print(traceback.format_exc())
                        print('Modulo não localizado')
                        dead.append(t)
                        continue

                    # ids = modulo().intervalos(uf, plataforma, data_varredura, self.tasklist[t]['tipo'], self.tasklist[t]['and'], self.tasklist[t]['base'], qtd_threads, self.tasklist[t]['arquivo_morto'], self.tasklist[t]['grau'], tipo_mod, self.tasklist[t]['area'])
                    try:
                        ids = modulo().intervalos(uf, plataforma, data_varredura, self.tasklist[t]['tipo'], self.tasklist[t]['and'], self.tasklist[t]['base'], qtd_threads, self.tasklist[t]['arquivo_morto'], self.tasklist[t]['grau'], tipo_mod, self.tasklist[t]['area'])
                    except Exception as e:
                        tb = traceback.format_exc(limit=1)
                        print(tb)
                        running -= 1
                        continue

                    if len(ids) == 0:
                        del modulo
                        dead.append(t)
                        continue

                    running += 1
                    dead.append(t)
                    b_index = 0
                    for b in ids:
                        if len(ids[b]) > 0:
                            # print(b, ids[b])
                            for i in range(0, len(ids[b])):
                                id_proc = str(uuid.uuid1()) + str(i) + str(b_index)
                                id_inicial = ids[b][i]
                                id_final = ids[b][i + 1] - 1 if i + 1 < len(ids[b]) else False
                                new_tasks[id_proc] = self.tasklist[t].copy()
                                new_tasks[id_proc]['running'] = False
                                new_tasks[id_proc]['iid'] = id_proc
                                new_tasks[id_proc]['base'] = b
                                # modulo = getattr(importlib.import_module('Controllers.' + plataforma.capitalize() + '.' + uf), uf)
                                wd = modulo()
                                if uf == '*':
                                    nome_tipo = new_tasks[id_proc]['tipo'].replace(' ','')
                                else:
                                    nome_tipo = new_tasks[id_proc]['tipo']
                                new_tasks[id_proc]['task'] = mp.Process(target=wd.ciclo, args=(data_varredura, nome_tipo, new_tasks[id_proc]['and'], b, new_tasks[id_proc]['categoria'], new_tasks[id_proc]['headless'], new_tasks[id_proc]['arquivo_morto'], [id_inicial, id_final], new_tasks[id_proc]['grau'], self.usuario, new_tasks[id_proc]['area'], new_tasks[id_proc]['vespertino']))
                                tv_grau = new_tasks[id_proc]['grau'] if new_tasks[id_proc]['grau'] is not None else '-'

                                if uf not in self.folders:
                                    self.folders[uf] = self.treeview.insert(parent='', index='end', text=uf, values=("", "", "", "", "", "", ""), open=True)
                                else:
                                    self.treeview.item(self.folders[uf], values=("", "", "", "", "", "", ""))

                                self.treeview.insert(parent=self.folders[uf], index='end', text=uf, iid=id_proc, values=(plataforma, b, str(i),  tv_grau, new_tasks[id_proc]['tipo'], "Analisando", id_proc))
                                del wd

                        b_index += 1
                    del modulo

            for d in dead:
                try:
                    self.treeview.delete(d)
                except:
                    print('Não é possível remover item da árvore')
                    pass
                if self.tasklist[d]['UF'] in self.folders:
                    children = self.treeview.get_children(self.folders[self.tasklist[d]['UF']])
                    if len(children) == 0:
                        self.treeview.delete(self.folders[self.tasklist[d]['UF']])
                        del self.folders[self.tasklist[d]['UF']]
                del self.tasklist[d]

            if len(new_tasks) > 0:
                self.tasklist = {**new_tasks, **self.tasklist}

    def check_unico(self, dead, task, task_id):
        for tsk in self.tasklist:
            if task_id != tsk and task['plataforma'] == self.tasklist[tsk]['plataforma']:
                if self.tasklist[tsk]['UF'] == task['UF']:
                    if task['base'] == self.tasklist[tsk]['base'] and task['tipo'] == self.tasklist[tsk]['tipo']:
                        if tsk not in dead:
                            return True

        return False

    def check_outras_bases(self, task):
        for tsk in self.tasklist:
            if task['plataforma'] == self.tasklist[tsk]['plataforma'] and self.tasklist[tsk]['UF'] == task['UF']:
                if task['base'] != self.tasklist[tsk]['base']:
                    if (self.tasklist[tsk]['task'] and self.tasklist[tsk]['task'].is_alive()) or (
                            task['grau'] == 2 and self.tasklist[tsk]['grau'] == 1):
                        return True

        return False

    def __init__(self, master, *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)
        self.parent = master
        # self.q = Queue(maxsize=0)
        self.lista = Queue(maxsize=0)
        self.tasklist = {}
        self.tasks_to_del = []
        self.new_tasklist = {}
        # CAPTURA CONFIG
        config = ConfigParser()

        base_dir = Path(__file__).resolve().parent.parent
        config.read(str(base_dir.joinpath('local.ini')))
        instancias = config.getint('form', 'instancias')
        instancias = instancias-1
        acao = config.getint('form', 'acao')
        tipo = config.getint('form', 'tipo')
        self.exige_senha = config.getboolean('form', 'exige_senha')
        self.default_user = config.get('form', 'user')
        self.agenda = config.getboolean('form', 'agenda')
        self.agenda_config = json.loads(config.get("form", "agendamentos"))

        self.list_listener_thread = threading.Thread(target=self.list_listener, args=(self.lista,))
        self.list_listener_thread.daemon = True
        self.list_listener_thread.start()

        # main_task = mp.Process(target=self.rodar_teste, args=(self.return_dict,))
        # main_task.start()
        master.title("BIGHERO")
        master.geometry("900x500")
        tabControl = ttk.Notebook(master, height=500)
        tab1 = ttk.Frame(tabControl)
        tab2 = ttk.Frame(tabControl)
        tab3 = ttk.Frame(tabControl)
        # tab4 = ttk.Frame(tabControl)

        menubar = Menu(master)
        self.master.config(menu=menubar)

        self.horaatual = BooleanVar()
        self.headless = BooleanVar()
        self.arquivo_morto = BooleanVar()
        self.detectar_data = BooleanVar()
        self.varredura_vespertina = BooleanVar()
        self.detectar_data.set(True)
        fileMenu = Menu(menubar, tearoff=0)
        fileMenu.add_checkbutton(label="Utilizar a Hora Atual", variable=self.horaatual)
        fileMenu.add_checkbutton(label="Varrer em modo headless", variable=self.headless)
        fileMenu.add_checkbutton(label="Varrer Arquivo Morto", variable=self.arquivo_morto)
        fileMenu.add_checkbutton(label="Detectar Data Automaticamente", variable=self.detectar_data, )
        fileMenu.add_checkbutton(label="Varredura Vespertina", variable=self.varredura_vespertina, )
        menubar.add_cascade(label="Opções", menu=fileMenu)
        menubar.add_command(label="Sair", command=self.close)

        tabControl.add(tab1, text='Tribunais')
        tabControl.add(tab2, text='Clientes')
        tabControl.add(tab3, text='Relatórios')
        # tabControl.add(tab4, text='Gestão')
        tabControl.pack(expand=1, fill="both")
        fonte = ("Verdana", "8")

        self.area = IntVar()
        self.rb_civel = Radiobutton(tab1, text="Cível", variable=self.area, value=1, command=self.sel_area)
        self.rb_civel.place(x=5, y=0)

        self.rb_trab = Radiobutton(tab1, text="Trabalhista", variable=self.area, value=2, command=self.sel_area)
        self.rb_trab.place(x=75, y=0)

        self.rb_trab = Radiobutton(tab1, text="Federal", variable=self.area, value=3, command=self.sel_area)
        self.rb_trab.place(x=185, y=0)

        self.area.set(1)

        # ABA DE FUNÇÕES DE VARREDURA DOS TRIBUNAIS
        Label(tab1, text="Ação:").place(x=5, y=30)
        # hoje_usa = date.today()
        # hoje_br = hoje_usa.strftime('%d/%m/%Y')
        self.tipoVarredura = StringVar()
        self.selTipoVarredura = Combobox(tab1, values=['Baixar', 'Varrer', 'Baixar e Varrer'], textvariable=self.tipoVarredura)
        self.selTipoVarredura.place(x=50, y=30)
        # self.selTipoVarredura.grid(column=0, row=0, padx = 0, pady = 5)
        self.selTipoVarredura["width"] = 10
        self.selTipoVarredura.current(acao)

        Label(tab1, text="Tipo:").place(x=170, y=30)
        self.cat_varredura = StringVar()
        self.selCateg = Combobox(tab1, values=['Parcial', 'Completa', 'Sem Movs'], textvariable=self.cat_varredura)
        self.selCateg.place(x=210, y=30)
        self.selCateg["width"] = 10
        self.selCateg.current(tipo)

        Label(tab1, text="Data:").place(x=330, y=30)
        self.data_var = StringVar()
        self.txtData = Entry(tab1, textvariable=self.data_var, width=15)
        self.txtData.place(x=380, y=30)
        # self.txtData.grid(column=20, row=0, padx=0, pady=5)
        # self.txtData["width"] = 15
        # self.txtData["height"] = 15
        self.txtData["font"] = fonte

        Label(tab1, text="Query adicional:").place(x=520, y=30)
        self.query_var = StringVar()
        self.txtQry = Entry(tab1, textvariable=self.query_var)
        self.txtQry.place(x=640, y=30)
        self.txtQry["width"] = 30
        self.txtQry["font"] = fonte

        Label(tab1, text="UF:").place(x=5, y=65)
        self.ufs = StringVar()
        self.selUF = Combobox(tab1, values=['Todos','AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI',
               'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SP', 'SE', 'TO','TRT'], textvariable=self.ufs)
        self.selUF.place(x=35, y=65)
        self.selUF["width"] = 10
        self.selUF.current(5)

        Label(tab1, text="Plataforma:").place(x=150, y=65)
        # ttk.Label(tab1, text ="Plataforma:").grid(column = 0, row = 1, padx = 0, pady = 15)
        self.plt = StringVar()
        self.selPlat = Combobox(tab1, values=['Todas','PJE', 'Eproc', 'Projudi', 'Esaj', 'Tucujuris', 'Fisico', 'Ppe'], textvariable=self.plt)
        self.selPlat.place(x=240, y=65)
        self.selPlat["width"] = 10
        self.selPlat.current(1)

        Label(tab1, text="Base:").place(x=360, y=65)
        self.base = StringVar()
        self.selBase = Combobox(tab1, values=['Todas', 'bec', 'ede', 'rek', 'hasson'], textvariable=self.base)
        self.selBase.place(x=410, y=65)
        self.selBase["width"] = 10
        self.selBase.current(0)

        Label(tab1, text="Grau:").place(x=530, y=65)
        self.grau = StringVar()
        self.selGrau = Combobox(tab1, values=['1º Grau', '2º Grau', 'Ambos'], textvariable=self.grau)
        self.selGrau.place(x=580, y=65)
        self.selGrau["width"] = 10
        self.selGrau.current(0)

        self.btnRodar = Button(tab1, text="Iniciar", font=fonte, width=10, command=self.btn_rodar_func)
        self.btnRodar.place(x=700, y=65)

        # self.listbox_running = Listbox(tab1, height=4)
        # self.listbox_running.grid(column=0, row=2, padx=0, pady=5, columnspan=40)
        #
        # self.listbox_queue = Listbox(tab1, height=4)
        # self.listbox_queue.grid(column=15, row=2, padx=0, pady=5, columnspan=40)

        self.btnEncerrar = Button(tab1, text="ENCERRAR PROCESSO", font=fonte, width=20, command=self.btn_encerrar)
        self.btnEncerrar.place(x=5, y=380)

        self.lblInst = Label(tab1, text="Instâncias:", width=8)
        self.lblInst.place(x=5, y=410)

        self.instancias = IntVar()
        self.selInst = Combobox(tab1, values=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16], textvariable=self.instancias)
        self.selInst.place(x=85, y=410)
        self.selInst["width"] = 10
        self.selInst.current(instancias)

        self.btnRodarTudo = Button(tab1, text="Rodar Tudo", font=fonte, width=10, command=lambda: self.btn_rodar_func(True))
        self.btnRodarTudo.place(x=205, y=410)

        self.btnEncerrarTudo = Button(tab1, text="Encerrar Tudo", font=fonte, width=12, command=self.btn_encerrar_tudo)
        self.btnEncerrarTudo.place(x=605, y=410)

        self.treeview = ttk.Treeview(tab1, height=12)
        self.treeview.place(x=0, y=110)
        self.treeview["columns"] = ("plt", "base","indice","grau","tipo","status","id")
        self.treeview.column("#0", width=70, minwidth=70)
        self.treeview.column("plt", width=130, minwidth=130)
        self.treeview.column("base", width=80, minwidth=50)
        self.treeview.column("indice", width=100, minwidth=50)
        self.treeview.column("grau", width=100, minwidth=50)
        self.treeview.column("tipo", width=100, minwidth=50)
        self.treeview.column("status", width=150, minwidth=150)
        self.treeview.column("id", width=400, minwidth=200)

        self.treeview.heading("#0", text="UF", anchor=tk.W)
        self.treeview.heading("plt", text="Plataforma", anchor=tk.W)
        self.treeview.heading("base", text="Base", anchor=tk.W)
        self.treeview.heading("indice", text="Índice", anchor=tk.W)
        self.treeview.heading("grau", text="Grau", anchor=tk.W)
        self.treeview.heading("tipo", text="Tipo", anchor=tk.W)
        self.treeview.heading("status", text="Status", anchor=tk.W)
        self.treeview.heading("id", text="ID", anchor=tk.W)
        self.folders = {}

        ###################################################################
        # ABA DE FUNÇÕES DE VARREDURA DOS SISTEMAS DOS CLIENTES

        Label(tab2, text="Ação:").place(x=5, y=5)
        self.tipoVarreduraC = StringVar()
        self.selTipoVarreduraCli = Combobox(tab2, values=['Baixar', 'Varrer', 'Baixar e Varrer'], textvariable=self.tipoVarreduraC)
        self.selTipoVarreduraCli.place(x=50, y=5)
        self.selTipoVarreduraCli["width"] = 12
        self.selTipoVarreduraCli.current(acao)

        Label(tab2, text="Tipo:").place(x=170, y=5)
        self.cat_varreduraC = StringVar()
        self.selCategCli = Combobox(tab2, values=['Varredura', 'Entrantes', 'Entrantes Ocorrencia', 'Atas', 'Pagamentos', 'Ocorrencias DJ', 'Ocorrencias TJ','Ocorrencias Titanium', 'SPIC', 'Contingencia', 'Provisionamento', 'Arquivamento'], textvariable=self.cat_varreduraC)
        self.selCategCli.place(x=210, y=5)
        self.selCategCli["width"] = 20
        self.selCategCli.current(0)

        Label(tab2, text="Query adicional:").place(x=520, y=5)
        self.query_varC = StringVar()
        self.txtQryCli = Entry(tab2, textvariable=self.query_varC)
        self.txtQryCli.place(x=640, y=8)
        self.txtQryCli["width"] = 28
        self.txtQryCli["font"] = fonte

        Label(tab2, text="Data:").place(x=5, y=40)
        self.data_varC = StringVar()
        self.txtDataCli = Entry(tab2, textvariable=self.data_varC, width=15)
        self.txtDataCli.place(x=50, y=40)
        self.txtDataCli["font"] = fonte

        Label(tab2, text="Plataforma:").place(x=170, y=40)
        # ttk.Label(tab1, text ="Plataforma:").grid(column = 0, row = 1, padx = 0, pady = 15)
        self.pltC = StringVar()
        self.selPlatCli = Combobox(tab2, values=['Processum','Espaider'], textvariable=self.pltC)
        self.selPlatCli.place(x=250, y=40)
        self.selPlatCli["width"] = 10
        self.selPlatCli.current(0)

        Label(tab2, text="Base:").place(x=360, y=40)
        self.baseC = StringVar()
        self.selBaseCli = Combobox(tab2, values=['Todas', 'bec', 'ede', 'rek', 'hasson'], textvariable=self.baseC)
        self.selBaseCli.place(x=410, y=40)
        self.selBaseCli["width"] = 10
        self.selBaseCli.current(0)

        self.btnRodarCli = Button(tab2, text="Iniciar", font=fonte, width=10, command=self.btn_rodar_cli)
        self.btnRodarCli.place(x=700, y=40)

        ###################################################################
        # ABA DE FUNÇÕES DE LOG
        Label(tab3, text="Tipo:").place(x=5, y=5)
        self.tipoLog = StringVar()
        self.selTipoLog = Combobox(tab3, values=['INFO', 'ERROR', 'WARNING'], textvariable=self.tipoLog)
        self.selTipoLog.place(x=50, y=5)
        self.selTipoLog["width"] = 10
        self.selTipoLog.current(0)

        Label(tab3, text="Sistema:").place(x=170, y=5)
        self.pltLog = StringVar()
        self.selPlatLog = Combobox(tab3, values=['Processum', 'Espaider', 'PJE', 'Eproc', 'Projudi', 'Esaj', 'Tucujuris', 'Fisico', 'Ppe'], textvariable=self.pltLog)
        self.selPlatLog.place(x=240, y=5)
        self.selPlatLog["width"] = 10
        self.selPlatLog.current(0)

        Label(tab3, text="Data Inicial:").place(x=350, y=5)
        self.data_i_log = StringVar()
        self.txtDataILog = Entry(tab3, textvariable=self.data_i_log)
        self.txtDataILog.place(x=440, y=5)
        self.txtDataILog["width"] = 15
        self.txtDataILog["font"] = fonte
        self.txtDataILog.insert(0, "2022-08-15")

        Label(tab3, text="Data Final:").place(x=550, y=5)
        self.data_f_log = StringVar()
        self.txtDataFLog = Entry(tab3, textvariable=self.data_f_log)
        self.txtDataFLog.place(x=640, y=5)
        self.txtDataFLog["width"] = 15
        self.txtDataFLog["font"] = fonte
        self.txtDataFLog.insert(0, "2022-08-16")

        self.btnLog = Button(tab3, text="Filtrar", font=fonte, width=10, command=self.btn_filtrar_log)
        self.btnLog.place(x=800, y=5)

        self.txtStatus = scrolledtext.ScrolledText(tab3)
        self.txtStatus["font"] = fonte
        self.txtStatus.place(x=5, y=40)
        self.txtStatus["height"] = 25
        self.txtStatus["width"] = 100

        # self.txtStatus = scrolledtext.ScrolledText(tab3)
        # self.txtStatus["font"] = fonte
        # self.txtStatus.place(x=10, y=110)
        # # self.txtStatus.place(x=10, y=110)
        # # self.txtStatus["state"] = "disabled"
        # self.txtStatus["height"] = 50

        # self.txtStatus = scrolledtext.ScrolledText(tab3)
        # self.txtStatus["font"] = fonte
        # self.txtStatus.grid(column=0, row=10)
        # # self.txtStatus.place(x=10, y=110)
        # # self.txtStatus["state"] = "disabled"
        # self.txtStatus["height"] = 20
        self.password_form()

    def btn_filtrar_log(self):
        dadosLog = [('2022-08-16 13:18:52.907','INFO','Varrendo Processo','gsantos','TBR00721','processum','*','rek','200551','201.47.170.196'),
                    ('2022-08-16 13:18:50.510','INFO','Varrendo Processo','gsantos','TBR00677','processum','*','bec','229226','201.47.170.196'),]

        for l in dadosLog:
            if self.tipoLog.get() == l[1]:
                self.txtStatus.insert('end', l[0] + ', '+l[3] + ', '+l[4] + ', '+l[7] + ', '+l[2]+ ', '+l[9] +'\n')

        return True

    def sel_area(self):
        area = self.area.get()
        if area == 1:
            self.selUF['values'] = ['Todos','AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI',
               'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SP', 'SE', 'TO']
            self.ufs.set('AC')

            self.selPlat['values'] = ['Todas', 'PJE', 'Eproc', 'Projudi', 'Esaj', 'Tucujuris', 'Fisico', 'Ppe']
            self.plt.set('PJE')
        elif area == 2:
            self.selUF['values'] = ['Todos', 'TRT01', 'TRT02', 'TRT03', 'TRT04', 'TRT05','TRT06', 'TRT07', 'TRT08', 'TRT09', 'TRT10', 'TRT11', 'TRT12',
                                    'TRT13','TRT14', 'TRT15', 'TRT16', 'TRT17','TRT18', 'TRT19', 'TRT20', 'TRT21', 'TRT22', 'TRT23', 'TRT24', 'TST']
            self.ufs.set('TRT01')
            self.selPlat['values'] = ['Todas', 'PJE', 'TST']
            self.plt.set('PJE')
        else:
            self.selUF['values'] = ['Todos', 'TRF01', 'TRF02', 'TRF03', 'TRF04', 'TRF05']
            self.ufs.set('TRF01')
            self.selPlat['values'] = ['Todas', 'PJE', 'Eproc','Fisico']
            self.plt.set('PJE')

    # FUNÇÃO DO BOTÃO PARA INICIAR A VARREDURA DO CLIENTE
    def btn_rodar_cli(self, varrer_todos=False):
        plataforma = self.pltC.get()
        base = self.baseC.get()
        hl = self.headless.get()
        query_and = self.query_varC.get()
        dia = self.data_varC.get().strip()

        arquivo_morto = self.arquivo_morto.get()

        tipo = self.cat_varreduraC.get()
        if dia == '':
            dia = None

        self.criar_varredura_cliente(plataforma, base, hl, arquivo_morto, dia, query_and, tipo)
        # if '*' not in self.folders:
        #     self.folders['*'] = self.treeview.insert(parent='', index='end', text='*', values=("", "", "", "", "Analisando", ""), open=True)
        # else:
        #     self.treeview.item(self.folders["*"], values=("", "", "", "", "Analisando", ""))
        #
        # iid = str(uuid.uuid1())
        # self.new_tasklist[iid] = {'UF': '*', 'task': False, 'base': base, 'plataforma': plataforma, 'grau': None,
        #                           'dia': dia, 'tipo': tipo, 'and': query_and, 'headless': hl,
        #                           'hora_atual': None, 'arquivo_morto': arquivo_morto, 'categoria': 2, 'area': '*'}
        # self.treeview.insert(parent=self.folders['*'], index='end', text='*', iid=iid, values=(plataforma, base, 0, None, "Aguardando", iid))

    # FUNÇÃO DO BOTÃO PARA INICIAR A VARREDURA
    def criar_varredura_cliente(self, plataforma, base, hl, arquivo_morto, dia, query_and, tipo):
        if '*' not in self.folders:
            self.folders['*'] = self.treeview.insert(parent='', index='end', text='*', values=("", "", "", "", "", "Analisando", ""), open=True)
        else:
            self.treeview.item(self.folders["*"], values=("", "", "", "", "", "Analisando", ""))

        if plataforma == 'Espaider':
            unicos = ('SPIC', 'Entrantes', 'Entrantes Ocorrencia', 'Ocorrencias TJ', 'Atas',)
        else:
            unicos = ('SPIC', 'Entrantes', 'Entrantes Ocorrencia', 'Ocorrencias TJ', 'Atas', 'Pagamentos')

        iid = str(uuid.uuid1())
        self.new_tasklist[iid] = {'UF': '*', 'task': False, 'base': base, 'plataforma': plataforma, 'grau': None,
                                  'dia': dia, 'tipo': tipo, 'and': query_and, 'headless': hl,
                                  'hora_atual': None, 'arquivo_morto': arquivo_morto, 'categoria': 2, 'area': '*', 'unico':tipo in unicos, 'vespertino':False}
        self.treeview.insert(parent=self.folders['*'], index='end', text='*', iid=iid, values=(plataforma, base, 0, None, tipo, "Aguardando", iid))

    # FUNÇÃO DO BOTÃO PARA INICIAR A VARREDURA
    def btn_rodar_func(self, varrer_todos=False):
        uf = self.ufs.get()
        plataforma = self.plt.get()
        grau = self.grau.get()
        base = self.base.get()
        hl = self.headless.get()
        hora_atual = self.horaatual.get()
        arquivo_morto = self.arquivo_morto.get()
        dia = self.data_var.get().strip()
        query_and = self.query_var.get()
        cat = self.cat_varredura.get()
        tipo = self.tipoVarredura.get()
        area = self.area.get()
        vespertino = self.varredura_vespertina.get()
        if vespertino:
            hora_atual = True

        if dia == '':
            dia = None

        self.criar_varredura(area, uf, plataforma, grau, base, hl, hora_atual, arquivo_morto, dia, query_and, cat, tipo, varrer_todos, vespertino=vespertino)

    # FUNÇÃO DO BOTÃO PARA INICIAR A VARREDURA
    def criar_varredura(self, area, uf, plataforma, grau, base, hl, hora_atual, arquivo_morto, dia, query_and, cat, tipo, varrer_todos=False, unico=False, vespertino=False):
        tipos = {'Baixar e Varrer': 3, 'Baixar': 1, 'Varrer': 2}
        graus = {'1º Grau': 1, '2º Grau': 2, 'Ambos': 0}
        cats = {'Sem Movs': 3, 'Completa': 2, 'Parcial': 1}
        uf_origem = uf
        print('iniciado varredura')
        detectar_data = self.detectar_data.get()
        if detectar_data:
            if not arquivo_morto:
                hoje = datetime.now()
                dia_da_semana = hoje.isoweekday()

                if (dia_da_semana == 5 and hoje.hour >= 18) or dia_da_semana in (6,7):
                    arquivo_morto = True

        if varrer_todos or uf_origem == 'Todos' or plataforma == 'Todas':
            # area = self.area.get()
            if area == 1:
                procs = {
                         'PJE': ('AP','BA','CE','ES','MA','MG','MT','PA','PB','PE','PI','RN','RO','RJ'),
                         'Eproc': ('SC', ),
                         'Tucujuris': ('AP',),
                         'Projudi': ('RR', 'PR', 'AM', 'PA', 'MA', 'PI', 'MG', 'ES','GO'),
                         'Esaj': ('BA','AC', 'AL', 'AM', 'CE', 'MS', 'SC', 'SP','RN'),
                         'Fisico': ('DF','PI','PB'),
                         'Ppe': ('RS','RJ',)
                }
            else:
                procs = {'PJE': ('TRT01','TRT02','TRT03','TRT04','TRT05','TRT06','TRT07','TRT08','TRT09','TRT10','TRT11','TRT12','TRT13','TRT14','TRT15','TRT16','TRT17','TRT18', 'TRT19', 'TRT20', 'TRT21', 'TRT22', 'TRT23', 'TRT24'),
                        }
        else:
            procs = {plataforma: (uf,),}

        for plat in procs:
            if not varrer_todos and plataforma != 'Todas':
                if plat != plataforma:
                    continue

            for uf in procs[plat]:
                if varrer_todos and plat == 'PJE':
                    continue

                if not varrer_todos and uf_origem != 'Todos':
                    if uf != uf_origem:
                        continue
                # ids_task = mp.Process(target=rodar, args=(self.lista, uf, plat, grau, dia, tipos[tipo], query_and, hl, hora_atual, arquivo_morto, base, cats[cat]))
                # ids_task.start()
                # self.procs.append(ids_task)
                # self.procs[self.total_procs].start()
                # self.total_procs += 1

                if uf not in self.folders:
                    self.folders[uf] = self.treeview.insert(parent='', index='end', text=uf, values=("", "", "", graus[grau], "", "Analisando", ""), open=True)
                else:
                    self.treeview.item(self.folders[uf], values=("", "", "", "", "", "Analisando", ""))

                r1 = 1 if graus[grau] == 0 else graus[grau]
                r2 = 3 if graus[grau] == 0 else graus[grau]+1
                for i in range(r1,r2):
                    iid = str(uuid.uuid1())
                    if area == 2 and plat == 'PJE':
                        plat = 'TRT'
                    # if area == 3 and plat == 'PJE':
                    #     plat = 'TRF'

                    self.new_tasklist[iid] = {'UF': uf, 'task': False, 'base': base, 'plataforma': plat, 'grau': i,
                                          'dia':dia, 'tipo': tipos[tipo], 'and': query_and, 'headless':hl, 'area': area,
                                          'hora_atual': hora_atual, 'arquivo_morto':arquivo_morto, 'categoria': cats[cat], 'unico': unico, 'vespertino': vespertino}
                    self.treeview.insert(parent=self.folders[uf], index='end', text=uf, iid=iid, values=(plat, base, 0, i, tipos[tipo], "Aguardando", iid))

    # FUNÇÃO DO BOTÃO PARA ENCERRAR VARREDURA DO PROCESSO SELECIONADO
    def btn_encerrar(self):
        curItem = self.treeview.focus()
        # item = self.treeview.item(curItem)
        selected_items = self.treeview.selection()
        for selected_item in selected_items:
            children = self.treeview.get_children(selected_item)
            for c in children:
                self.tasks_to_del.append(c)

            if len(selected_item) > 15:
                self.tasks_to_del.append(selected_item)
            else:
                branch_text = self.treeview.item(selected_item)['text']
                del self.folders[branch_text]

            try:
                self.treeview.delete(selected_item)
            except:
                pass

    # FUNÇÃO DO BOTÃO PARA ENCERRAR VARREDURA DE TODOS OS PROCESSOS
    def btn_encerrar_tudo(self):
        listOfEntriesInTreeView = self.treeview.get_children()
        # print(listOfEntriesInTreeView)
        # selected_items = self.treeview.selection()
        for selected_item in listOfEntriesInTreeView:
            children = self.treeview.get_children(selected_item)
            for c in children:
                self.tasks_to_del.append(c)

            if len(selected_item) > 15:
                self.tasks_to_del.append(selected_item)
            else:
                branch_text = self.treeview.item(selected_item)['text']
                del self.folders[branch_text]

            try:
                self.treeview.delete(selected_item)
            except:
                pass


    def close(self):
        # self.tasks_to_del = self.tasklist[:]
        # self.btn_encerrar_tudo()
        for t in self.tasklist:
            try:

                parent_pid = self.tasklist[t]['task'].pid
                parent = psutil.Process(parent_pid)
                for child in parent.children(recursive=True):
                    try:
                        child.kill()
                    except:
                        pass
                self.tasklist[t]['task'].terminate()
            except:
                pass

        self.parent.destroy()
        sys.exit()

    def password_form(self):
        # TELA DE LOGIN
        self.top = Toplevel()
        self.top.geometry('300x200')
        self.top.title('BIGHERO')
        self.top.configure(background='white')
        # frame for window margin
        parent = Frame(self.top, padx=10, pady=10)
        parent.pack(fill=BOTH, expand=True)
        # parent.configure(background='white')
        # entrys with not shown text
        Label(parent, text="Usuário:").pack(side=TOP)
        # Label(tab1, text="Ação:").place(x=5, y=5)
        self.user = Entry(parent)
        self.user.config(width=16)
        self.user.pack(side=TOP, padx=0, fill=BOTH)
        Label(parent, text="Senha:").pack(side=TOP)
        self.password = Entry(parent, show='*')
        self.password.config(width=16)
        self.password.pack(side=TOP, padx=0, fill=BOTH)

        self.login_msgbox = StringVar()
        msgs = Message(parent, textvariable=self.login_msgbox, justify='left', width=280)
        # msgs.config(width=5000)
        msgs.pack(fill=BOTH)

        # button to attempt to login
        self.btnLogin = Button(parent, text="Login", width=10, pady=6, command=self.check_password)
        self.btnLogin.pack(side=BOTTOM)
        self.user.bind('<Return>', self.login_enter)
        self.password.bind('<Return>', self.login_enter)
        self.user.focus_set()

        if not self.exige_senha:
            self.check_password()

        # self.usuario = 'admin'
        # self.parent.deiconify()
        # self.top.destroy()
        # parent.protocol("WM_DELETE_WINDOW", self.close)

    def check_password(self):
        self.login_msgbox.set("Processando login...")
        user = self.default_user
        password = ''
        if self.exige_senha:
            user = self.user.get()
            password = self.password.get()
            if user == '':
                self.login_msgbox.set("Preencha o campo de login")
                return
            if password == '':
                self.login_msgbox.set("Preencha o campo de senha")
                return
        self.btnLogin['state'] = DISABLED
        self.user['state'] = DISABLED
        self.password['state'] = DISABLED

        login = threading.Thread(target=self.autentica, args=(user, password))
        login.start()

    def autentica(self, user, password, failures=[]):
        # self.usuario = 'admin'
        # self.parent.deiconify()
        # self.top.destroy()
        varr_cl = getattr(importlib.import_module('Controllers.varredura'), 'Varredura')
        user_data = varr_cl().autentica_user(user, password) if self.exige_senha else {'usr_nome': user, }

        if user_data:
            # self.login_msgbox.set("Login Realizado")
            self.login_msgbox.set("Vinculando Logs")
            varr_cl().vincula_logs()
            # time.sleep(2)
            # self.login_msgbox.set("Vinculando Logs")
            # time.sleep(2)
            self.usuario = user_data['usr_nome']
            self.parent.deiconify()
            self.top.destroy()

            # INICIA THREAD DE AGENDAMENTOS
            if self.agenda:
                self.get_schedules()

            return

        del varr_cl

        failures.append(1)
        if sum(failures) >= 3:
            # self.parent.destroy()
            self.close()
            raise SystemExit('Unauthorized login attempt')
        else:
            self.login_msgbox.set('Tente novamente. %i/%i' % (sum(failures), 3))

        try:
            self.btnLogin['state'] = NORMAL
            self.user['state'] = NORMAL
            self.password['state'] = NORMAL
        except:
            pass


    def login_enter(self, event):
        self.check_password()

    def agendamentos(self, tipo):
        if tipo == 'PjeBec':
            self.criar_varredura(1, 'Todos', 'PJE', '1º Grau', 'bec', False, False, False, '', '', 'Parcial', 'Baixar e Varrer')
        if tipo == '2gPje':
            self.criar_varredura(1, 'Todos', 'PJE', '2º Grau', 'Todas', False, False, False, '', '', 'Parcial', 'Baixar e Varrer')
        if tipo == '2gEsaj':
            self.criar_varredura(1, 'Todos', 'Esaj', '2º Grau', 'Todas', False, False, False, '', '', 'Parcial', 'Baixar e Varrer')
        if tipo == '2gProjudi':
            self.criar_varredura(1, 'Todos', 'Projudi', '2º Grau', 'Todas', False, False, False, '', '', 'Parcial','Baixar e Varrer')
        if tipo == '2gEproc':
            self.criar_varredura(1, 'Todos', 'Eproc', '2º Grau', 'Todas', False, False, False, '', '', 'Parcial','Baixar e Varrer')
        if tipo == 'BAede':
            self.criar_varredura(1, 'BA', 'Todas', '1º Grau', 'ede', False, False, False, '', '', 'Parcial', 'Baixar e Varrer')
        if tipo == 'TRTtodos':
            self.criar_varredura(2, 'Todos', 'PJE', '1º Grau', 'Todas', False, False, False, '', '', 'Parcial', 'Baixar e Varrer')
        if tipo == 'TRTtodos2g':
            self.criar_varredura(2, 'Todos', 'PJE', '2º Grau', 'Todas', False, False, False, '', '', 'Parcial', 'Baixar e Varrer')
        if tipo == 'Civeltodos':
            self.criar_varredura(1, 'Todos', 'Todas', '1º Grau', 'Todas', False, False, False, '', '', 'Parcial', 'Baixar e Varrer')
        if tipo == 'ComCaptcha':
            self.criar_varredura(1, 'BA', 'Projudi', '1º Grau', 'ede', False, False, False, '', '', 'Parcial', 'Baixar e Varrer')
            self.criar_varredura(1, 'RS', 'Eproc', '1º Grau', 'rek', False, False, False, '', '', 'Parcial','Baixar e Varrer')
            self.criar_varredura(1, 'TO', 'Eproc', '1º Grau', 'bec', False, False, False, '', '', 'Parcial', 'Baixar e Varrer')
            self.criar_varredura(1, 'SE', 'Ppe', '1º Grau', 'rek', False, False, False, '', '', 'Parcial', 'Baixar e Varrer')
            self.criar_varredura(1, 'MG', 'Fisico', '1º Grau', 'rek', False, False, False, '', '', 'Parcial', 'Baixar e Varrer')
            self.criar_varredura(1, 'MT', 'Projudi', '1º Grau', 'Todas', False, False, False, '', '', 'Parcial', 'Baixar e Varrer')
            self.criar_varredura(1, 'DF', 'Pje', '1º Grau', 'bec', False, False, False, '', '', 'Parcial', 'Baixar e Varrer')

        if tipo == 'Pagamentos':
            dia_da_semana = datetime.now().weekday()
            if dia_da_semana not in (5,6):
                self.criar_varredura_cliente('Processum', 'Todas', False, False, None, '', 'Pagamentos')
        if tipo == 'Atas':
            self.criar_varredura_cliente('Processum', 'Todas', False, False, None, '', 'Atas')
        if tipo == 'Arquivamento':
            self.criar_varredura_cliente('Processum', 'Todas', False, False, None, '', 'Arquivamento')
        if tipo == 'OcorrenciasDJ':
            self.criar_varredura_cliente('Processum', 'Todas', False, False, None, '', 'Ocorrencias DJ')
        if tipo == 'OcorrenciasTJ':
            self.criar_varredura_cliente('Processum', 'Todas', False, False, None, '', 'Ocorrencias TJ')
        if tipo == 'SPIC':
            self.criar_varredura_cliente('Processum', 'Todas', False, False, None, '', 'SPIC')
        if tipo == 'Entrantes':
            self.criar_varredura_cliente('Processum', 'Todas', False, False, None, '', 'Entrantes')
        if tipo == 'Contingencia':
            self.criar_varredura_cliente('Processum', 'Todas', False, False, None, '', 'Contingencia')
        if tipo == 'EntrantesOcorrencia':
            self.criar_varredura_cliente('Processum', 'Todas', False, False, None, '', 'Entrantes Ocorrencia')
        if tipo == 'EprocRS':
            self.criar_varredura(1, 'RS', 'Eproc', '1º Grau', 'rek', False, False, False, '', '', 'Parcial','Baixar e Varrer')
        if tipo == 'Espaider':
            self.criar_varredura_cliente('Espaider', 'ede', False, False, None, '', 'Varredura')
        if tipo == 'EntrantesEspaider':
            self.criar_varredura_cliente('Espaider', 'ede', False, False, None, '', 'Entrantes')
        if tipo == 'EntrantesOcorrenciaEspaider':
            self.criar_varredura_cliente('Espaider', 'ede', False, False, None, '', 'Entrantes Ocorrencia')

    def get_schedules(self):
        if 'EncerrarTudo' in self.agenda_config:
            schedule.every().day.at("17:58").do(self.btn_encerrar_tudo)

        if 'BAede' in self.agenda_config:
            schedule.every().day.at("18:00").do(self.agendamentos, 'BAede')

        if 'ComCaptcha' in self.agenda_config:
            schedule.every().day.at("18:00").do(self.agendamentos, 'ComCaptcha')

        if 'SegundoGrau' in self.agenda_config:
            schedule.every().day.at("03:00").do(self.agendamentos, '2gPje')
            schedule.every().day.at("04:00").do(self.agendamentos, '2gEsaj')
            schedule.every().day.at("04:20").do(self.agendamentos, '2gProjudi')
            schedule.every().day.at("04:40").do(self.agendamentos, '2gEproc')

        if 'PjeBec' in self.agenda_config:
            schedule.every().day.at("18:00").do(self.agendamentos, 'PjeBec')

        if 'Processum' in self.agenda_config:
            schedule.every().day.at("07:00").do(self.agendamentos, 'EntrantesOcorrencia')
            schedule.every().day.at("14:00").do(self.agendamentos, 'Entrantes')
            schedule.every().day.at("17:50").do(self.agendamentos, 'Entrantes')
            schedule.every().day.at("23:00").do(self.agendamentos, 'Entrantes')
            schedule.every().day.at("07:30").do(self.agendamentos, 'SPIC')
            schedule.every().day.at("00:00").do(self.agendamentos, 'OcorrenciasDJ')
            schedule.every().day.at("08:00").do(self.agendamentos, 'OcorrenciasTJ')
            schedule.every().day.at("12:00").do(self.agendamentos, 'Pagamentos')
            schedule.every().day.at("14:00").do(self.agendamentos, 'Pagamentos')
            schedule.every().day.at("16:00").do(self.agendamentos, 'Pagamentos')
            schedule.every().day.at("17:55").do(self.agendamentos, 'Pagamentos')
            schedule.every().day.at("19:00").do(self.agendamentos, 'Pagamentos')
            schedule.every().day.at("11:00").do(self.agendamentos, 'Atas')
            schedule.every().day.at("15:00").do(self.agendamentos, 'Atas')
            schedule.every().day.at("17:00").do(self.agendamentos, 'Atas')
            schedule.every().day.at("20:00").do(self.agendamentos, 'Atas')
            schedule.every().day.at("23:00").do(self.agendamentos, 'Atas')
            schedule.every().day.at("17:56").do(self.agendamentos, 'Arquivamento')
            schedule.every().day.at("09:00").do(self.agendamentos, 'Contingencia')
            schedule.every().day.at("15:00").do(self.agendamentos, 'Contingencia')
            schedule.every().day.at("17:40").do(self.agendamentos, 'Contingencia')

        if 'Espaider' in self.agenda_config:
            schedule.every().day.at("07:00").do(self.agendamentos, 'EntrantesOcorrenciaEspaider')
            schedule.every().day.at("14:10").do(self.agendamentos, 'EntrantesEspaider')
            schedule.every().day.at("17:40").do(self.agendamentos, 'EntrantesEspaider')
            schedule.every().day.at("23:10").do(self.agendamentos, 'EntrantesEspaider')
            schedule.every().day.at("08:30").do(self.agendamentos, 'Espaider')
            schedule.every().day.at("12:30").do(self.agendamentos, 'Espaider')
            schedule.every().day.at("15:30").do(self.agendamentos, 'Espaider')

        if 'EprocRS' in self.agenda_config:
            schedule.every().day.at("18:00").do(self.agendamentos, 'EprocRS')

        if 'TRT' in self.agenda_config:
            schedule.every().day.at("18:05").do(self.agendamentos, 'TRTtodos')
            schedule.every().day.at("00:05").do(self.agendamentos, 'TRTtodos2g')

        if 'Civeltodos' in self.agenda_config:
            schedule.every().day.at("18:30").do(self.agendamentos, 'Civeltodos')

        # schedule.every().day.at("14:24").do(self.agendamentos, 'Civeltodos')
        # schedule.every().tuesday.at("16:10").do(self.bb)
        # schedule.every().tuesday.at("16:11").do(self.cc)
        # schedule.every(10).seconds.do(self.agendamentos, '2g')
        while True:
            # Checks whether a scheduled task
            # is pending to run or not
            schedule.run_pending()
            time.sleep(1)


'''
RETORNA A DATA UTILIZADA COMO PARÂMETRO PARA VARREDURA
A VARREDURA TEM QUE OCORRER TODO DIA APÓS AS 18:00
CASO A HORA DE INICIO DA VARREDURA SEJA INFERIOR A 18, ENTÃO A DATA DE REFERENCIA SERA O DIA UTIL ANTERIOR AS 18:00
CASO SEJA SUPERIOR AS 18, SERÁ O DIA ATUAL AS 18:00
CASO O PARAMETRO DATA_ATUAL SEJA TRUE, RETORNARA A DATA E HORA ATUAL COMO REFERENCIA. DESSA MANEIRA TODA A BASE SERÁ VARRIDA
'''
def get_data_varredura(data_atual=False, dia=None):
    '''
    :param bool data_atual: retorna a data e hora atual
    '''
    hoje = datetime.now()

    if data_atual:
        return hoje.strftime('%Y-%m-%d %H:%M')

    dia_da_semana = hoje.weekday()

    if dia is not None and dia != '':
        return dia
        # dia = datetime.strptime(dia)
        # dia = datetime.strptime(dia, '%Y-%m-%d %H:%M')
        # return dia.strftime('%Y-%m-%d %H:%M')

    if dia_da_semana == 5:
        dia = hoje - timedelta(days=1)
    elif dia_da_semana == 6:
        dia = hoje - timedelta(days=2)
    else:
        hora = int(hoje.strftime('%H'))
        if hora < 18:
            if dia_da_semana == 0:
                dia = hoje - timedelta(days=3)
            else:
                dia = hoje - timedelta(days=1)
        else:
            dia = hoje

    return dia.strftime('%Y-%m-%d 18:00')

# if __name__ == "__main__":
#     root = tk.Tk()
#     MainApplication(root).pack(side="top", fill="both", expand=True)
#     root.mainloop()