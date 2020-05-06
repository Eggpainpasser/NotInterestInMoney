import tkinter as tk
import tkinter.font as tkFont
import json
from Binder import Binder
import random


class app_gui(object):
    def __init__(self):
        self.config_file            = './config.json'

        self.interval_key           = 'interval'
        self.select_key             = 'select_codes'
        self.min_pct_chg_key        = 'min_pct_chg'
        self.max_pct_chg_key        = 'max_pct_chg'
        self.tov_key                = 'tov'
        self.vor_key                = 'vor'
        self.quotes_key             = 'quotes'
        self.intvar_listall_key     = 'list_all'
        self.intvar_tech_key        = 'tech_open'
        self.alpha_key              = 'alpha'
        self.keys_key               = 'keys'
        self.started                = False
        self.after_event            = None

        self.loadconfig()
        self.alpha                  = self.config[self.alpha_key]
        self.keys                   = self.config[self.keys_key]

        self.reset()


    def loadconfig(self):
        config_fp                   = open(self.config_file,'rt',encoding='utf-8')
        self.config                 = json.load(config_fp)
        config_fp.close()

    def saveconfig(self):
        config_fp                   = open(self.config_file,'wt',encoding='utf-8')
        json.dump(self.config, config_fp)
        config_fp.close()    

    def select_quotes(self):
        Quotes = self.config['quotes']
        nquotes = len(Quotes)
        iquote = random.randint(0,nquotes - 1)
        return Quotes[iquote]     

    def BuildMainDialog(self):
        self.maindialog = tk.Tk()
        self.maindialog.title(self.select_quotes())
        self.maindialog.geometry('420x260-0-40')
        self.maindialog.resizable(0,0)
        self.maindialog.protocol("WM_DELETE_WINDOW", self.close_event_all)
        self.maindialog.attributes("-toolwindow",1)
        self.maindialog.attributes("-topmost", -1)
        self.maindialog.attributes("-alpha",self.alpha)
    
    def BuildComponentItemBox(self):
        assert self.maindialog is not None
        self.itembox      = tk.LabelFrame(self.maindialog, height=140, \
                width=200, padx=2, pady=2)
        self.itembox.place(x=10,y=10)

        self.codebox      = tk.Listbox(self.itembox, height=5, width=26,\
            relief='groove', bg = 'lightblue')
        select_codes   = self.config[self.select_key]
        self.codebox.delete(0,'end')
        for item in select_codes:
            self.codebox.insert('end', item)
        self.codebox.place(x=2, y=2)

        self.entry_operate  = tk.Entry(self.itembox, width=10)
        self.entry_operate.bind("<Return>",self.event_operate)
        self.entry_operate.place(x=2, y= 102)

        self.button_operate = tk.Button(self.itembox, height = 1, width = 15, \
                text='插入/删除',relief='groove')
        self.button_operate.bind("<Button-1>", self.event_operate)
        self.button_operate.place(x=78, y=100)

    def BuildComponentCheckBox(self):
        self.checkbox       = tk.LabelFrame(self.maindialog, height=140, \
                width=200, padx=2, pady=2)
        self.checkbox.place(x=210,y=10)
        
        self.label_interval = tk.Label(self.checkbox, text='间隔时间(秒)')
        self.label_interval.place(x=2,y=2)

        self.entry_interval = tk.Entry(self.checkbox, width=10)
        self.entry_interval.insert('end',str(self.config[self.interval_key]))
        self.entry_interval.place(x=110,y=2)

        self.label_pct_chg  = tk.Label(self.checkbox, text='涨跌幅范围')
        self.label_pct_chg.place(x=2,y=32)

        self.entry_pct_chg_min = tk.Entry(self.checkbox, width=5)
        self.entry_pct_chg_min.insert('end',str(self.config[self.min_pct_chg_key]))
        self.entry_pct_chg_min.place(x=100, y=32)

        self.entry_pct_chg_max = tk.Entry(self.checkbox, width=5)
        self.entry_pct_chg_max.insert('end',str(self.config[self.max_pct_chg_key]))
        self.entry_pct_chg_max.place(x=150, y=32)

        self.label_tov = tk.Label(self.checkbox, text='换手率')
        self.label_tov.place(x=2,y=62)

        self.entry_tov = tk.Entry(self.checkbox, width=5)
        self.entry_tov.insert('end',str(self.config[self.tov_key]))
        self.entry_tov.place(x=56, y=62)

        self.label_vor = tk.Label(self.checkbox, text='量比')
        self.label_vor.place(x=102, y=62)

        self.entry_vor = tk.Entry(self.checkbox, width=5)
        self.entry_vor.insert('end',str(self.config[self.vor_key]))
        self.entry_vor.place(x=150, y=62)

        self.intvar_listall = tk.IntVar()
        self.intvar_listall.set(self.config[self.intvar_listall_key])
        self.check_button_check_all = tk.Checkbutton(self.checkbox,text='展示全部',variable=self.intvar_listall)
        self.check_button_check_all.place(x=2,y=92)

        self.intvar_tech_check = tk.IntVar()
        self.intvar_tech_check.set(self.config[self.intvar_tech_key])
        self.check_button_tech_warn = tk.Checkbutton(self.checkbox,text='智能提示',variable=self.intvar_tech_check)
        self.check_button_tech_warn.place(x=92,y=92)

    def BuildComponentExtraBox(self):
        self.extrabox      = tk.LabelFrame(self.maindialog, height=110, \
            width=400, padx=2, pady=2)
        self.extrabox.bind("<MouseWheel>",self.event_change_alpha)
        self.extrabox.place(x=10,y=150)

        self.button_listen = tk.Button(self.extrabox, height=2,width=10,text='开始监听')
        self.button_listen.bind("<Button-1>", self.event_start)
        self.button_listen.place(x=165,y=20)

    def BuildShowDialog(self):
        self.showdialog = tk.Toplevel()
        self.showdialog.title(self.select_quotes())
        self.showdialog.geometry('300x600-0-40')
        self.showdialog.resizable(0,0)

        self.showdialog.protocol("WM_DELETE_WINDOW", self.close_event_stop)
        self.showdialog.attributes("-toolwindow",1)
        self.showdialog.attributes("-topmost", -1)
        self.showdialog.attributes("-alpha",self.alpha)
        
        self.showdialog.bind("<MouseWheel>",self.event_change_alpha)
        self.showdialog.withdraw()

        self.button_stop = tk.Button(self.showdialog,text='停止')
        self.button_stop.bind("<Button-1>", self.event_stop)
        self.button_stop.place(x=135,y=560)

    def BuildComponentShowBox(self):
        font         = tkFont.Font(family='楷体',size=12)
        self.showbox = tk.LabelFrame(self.showdialog, height=550, width=295,padx=2,pady=2)
        self.showbox.bind("<Motion>",self.event_motion_concept)
        self.showbox.place(x=2,y=2)

        self.indexboard = tk.Label(self.showbox, width=35, height=4,padx=2,pady=2,justify='left',relief = 'groove',anchor='nw',font=font)
        self.indexboard.bind("<Motion>",self.event_motion_concept)
        self.indexboard.place(x=2,y=2)

        self.conceptboard = tk.Label(self.showbox, width=35,height=11,padx=2,pady=2,justify='left',relief = 'groove',anchor='nw',font=font)
        self.conceptboard.bind("<Button-1>",self.event_click_concept)
        self.conceptboard.bind("<Motion>",self.event_motion_concept)
        self.conceptboard.place(x=2,y=80)


        self.stboard = tk.Label(self.showbox, width=35,height=16,padx=2,pady=2,justify='left',relief = 'groove',anchor='nw',font=font)
        self.stboard.bind("<Motion>",self.event_motion_concept)
        self.stboard.place(x=2,y=265)

    def BuildDetailDialog(self):
        font         = tkFont.Font(family='楷体',size=12)
        self.maxdetail_line = 15
        self.detail_window  = tk.Toplevel()
        self.detail_window.title(self.select_quotes())
        self.detail_window.geometry('50x50-0-0')
        self.detail_window.resizable(0,0)

        self.detail_window.protocol("WM_DELETE_WINDOW", self.detail_ignore_event)
        self.detail_window.attributes("-toolwindow",1)
        self.detail_window.attributes("-topmost", -1)
        self.detail_window.attributes("-alpha",self.alpha)

        self.detail_window.bind("<MouseWheel>",self.event_change_alpha)
        self.detail_window.bind("<Motion>",self.event_motion_concept)
        self.detail_window.withdraw()

        self.board = tk.Label(self.detail_window, width=35,height=self.maxdetail_line,padx=2,pady=2,justify='left',relief = 'groove',anchor='nw',font=font)
        self.board.place(x=2,y=2)


    def reset(self):
        self.BuildMainDialog()
        self.BuildComponentItemBox()
        self.BuildComponentCheckBox()
        self.BuildComponentExtraBox()
        self.BuildShowDialog()
        self.BuildComponentShowBox()
        self.BuildDetailDialog()

    def mainloop(self):
        self.maindialog.mainloop()

    def show_update(self):
        index_text   = self.bd.indexstr
        self.indexboard.config(text=index_text)

        concept_text = self.bd.conceptstr
        self.conceptboard.config(text=concept_text)

        st_text      = self.bd.ststr
        self.stboard.config(text=st_text)

        #update_text = self.bd.commit_str
        #self.text_show.config(text=update_text)
        self.after_event = self.showdialog.after(333, self.show_update)

    def event_change_alpha(self, event):
        if event.delta > 0:
            self.alpha = self.alpha + 0.02
            self.alpha = min(self.alpha, 1.0)
        else:
            self.alpha = self.alpha - 0.02
            self.alpha = max(self.alpha, 0.01)
        self.maindialog.attributes("-alpha",self.alpha)
        self.showdialog.attributes("-alpha",self.alpha)
        self.detail_window.attributes("-alpha",self.alpha)

    def event_operate(self, event):
        code_in_entry = self.entry_operate.get()
        if code_in_entry is '':
            selected_curse = self.codebox.curselection()
            for curse in selected_curse:
                remove_key = self.codebox.get(curse)
                self.codebox.delete(curse)
        else:
            operate = False
            for i in range(self.codebox.size()):
                if self.codebox.get(i) == code_in_entry:
                    self.codebox.delete(i)
                    operate = True
            if not operate:
                self.codebox.insert('end', code_in_entry)
            self.config[self.select_key] = self.codebox.get(0,'end')
            self.entry_operate.delete(0,'end')
    
    def event_start(self, event):
        if not self.started:
            try:
                interval_seconds = int(self.entry_interval.get())
            except Exception as e:
                interval_seconds = 5

            try:
                min_pct_chg     = float(self.entry_pct_chg_min.get())
                max_pct_chg     = float(self.entry_pct_chg_max.get())
            except Exception as e:
                min_pct_chg     = -5
                max_pct_chg     = 5

            try:
                tov_warn        = float(self.entry_tov.get())
            except Exception as e:
                tov_warn        = 3.0
            
            try:
                vor_warn        = float(self.entry_vor.get())
            except Exception as e:
                vor_warn        = 1.5


            self.maindialog.withdraw()
            self.bd = Binder(self.codebox.get(0,'end'),
                time_interval = interval_seconds, 
                pct_chg_limit = [min_pct_chg, max_pct_chg], 
                tov_limit = tov_warn, vor_limit = vor_warn,
                listall = self.intvar_listall.get(),
                keys = self.keys)
            self.bd.start()
            self.show_update()
            self.started = True
            self.showdialog.deiconify()
    
    def event_click_concept(self, event):
        if not self.bd:
            return
        click_id = (event.y - 2)//16
        if click_id == 0 or click_id >= 12:
            return
        lines = self.conceptboard["text"].split('\n')
        concept = lines[click_id].split(' ')[0]
        content, nline = self.bd.ConceptListStr(concept)
        if nline <= 1:
            return
        if self.detail_window is None:
            return
        width  = 300
        height = 16 * min(self.maxdetail_line, nline) + 10
        pointx = event.x_root - width - 50 if event.x_root - width - 50 > 0 else event.x_root
        pointy = event.y_root
        self.detail_window.title(concept)
        self.detail_window.geometry('%dx%d+%d+%d'%(width,height,pointx,pointy))
        self.board.config(text=content)
        self.detail_window.deiconify()
        
    
    def event_motion_concept(self, event):
        if not self.detail_window:
            return
        self.detail_window.withdraw()
        
    def detail_ignore_event(self):
        if not self.detail_window:
            return
        self.detail_window.withdraw()

    def close_event_stop(self):
        if self.started:
            self.showdialog.withdraw()
            self.detail_window.withdraw()
            if self.after_event:
                self.showdialog.after_cancel(self.after_event)
            self.bd.stop()
            self.started = False
            self.maindialog.deiconify()
    
    def close_event_all(self):
        self.config[self.interval_key]    = str(self.entry_interval.get())

        self.config[self.min_pct_chg_key] = str(self.entry_pct_chg_min.get())
        self.config[self.max_pct_chg_key] = str(self.entry_pct_chg_max.get())

        self.config[self.tov_key]         = str(self.entry_tov.get())
        self.config[self.vor_key]         = str(self.entry_vor.get()) 

        self.config[self.select_key]      = self.codebox.get(0,'end')

        self.config[self.intvar_listall_key]  = self.intvar_listall.get()
        self.config[self.intvar_tech_key]     = self.intvar_tech_check.get()

        self.saveconfig()

        self.close_event_stop()
        self.detail_window.destroy()
        self.showdialog.destroy()
        self.maindialog.destroy()

    def event_stop(self, event):
        self.close_event_stop()


def main():
    gui = app_gui()
    #gui.reset()
    gui.mainloop()


