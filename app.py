import sqlite3, os, csv, calendar, shutil, webbrowser
from datetime import datetime, date
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

APP_DIR = os.path.join(os.path.expanduser('~'), 'PayrollProData')
os.makedirs(APP_DIR, exist_ok=True)
DB = os.path.join(APP_DIR, 'payrollpro.db')
LOGO = os.path.join(APP_DIR, 'company_logo.png')
NAVY='#0b1220'; PANEL='#111b2e'; PANEL2='#17243a'; BLUE='#2f80ed'; TEXT='#eaf2ff'; MUTED='#9fb0c8'; GREEN='#27ae60'; RED='#e74c3c'; BORDER='#263754'; GOLD='#f2c94c'

class DBManager:
    def __init__(self):
        self.con=sqlite3.connect(DB); self.con.row_factory=sqlite3.Row; self.init()
    def init(self):
        c=self.con.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS employees(id INTEGER PRIMARY KEY AUTOINCREMENT, emp_no TEXT UNIQUE, name TEXT NOT NULL, nic TEXT, phone TEXT, branch TEXT, department TEXT, designation TEXT, joined TEXT, basic REAL DEFAULT 0, bank TEXT, account TEXT, epf_no TEXT, status TEXT DEFAULT 'Active')''')
        c.execute('''CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY AUTOINCREMENT, emp_id INTEGER, work_date TEXT, time_in TEXT, time_out TEXT, status TEXT DEFAULT 'Present', ot_hours REAL DEFAULT 0, note TEXT, UNIQUE(emp_id,work_date))''')
        c.execute('''CREATE TABLE IF NOT EXISTS payroll(id INTEGER PRIMARY KEY AUTOINCREMENT, emp_id INTEGER, month TEXT, basic REAL, allowances REAL, ot REAL, gross REAL, epf REAL, no_pay REAL, deductions REAL, net REAL, etf REAL, created TEXT, UNIQUE(emp_id,month))''')
        c.execute('''CREATE TABLE IF NOT EXISTS pay_items(id INTEGER PRIMARY KEY AUTOINCREMENT, emp_id INTEGER, month TEXT, category TEXT, item_type TEXT, amount REAL DEFAULT 0, note TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY, v TEXT)''')
        self.con.commit()
    def q(self,sql,args=(),one=False):
        cur=self.con.execute(sql,args); rows=cur.fetchone() if one else cur.fetchall(); self.con.commit(); return rows
    def setting(self,k,default=''):
        r=self.q('SELECT v FROM settings WHERE k=?',(k,),one=True); return r['v'] if r else default
    def set_setting(self,k,v): self.q('INSERT INTO settings(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v',(k,v))

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.db=DBManager(); super().title('PayrollPro — Sri Lanka Payroll & Attendance'); self.geometry('1320x800'); self.minsize(1120,680); self.configure(bg=NAVY)
        self.style=ttk.Style(self); self.style.theme_use('clam'); self.style.configure('.',background=PANEL,foreground=TEXT,fieldbackground=PANEL2,bordercolor=BORDER,font=('Segoe UI',10)); self.style.configure('Treeview',background=PANEL2,foreground=TEXT,fieldbackground=PANEL2,rowheight=31); self.style.configure('Treeview.Heading',background='#1d2d49',foreground=TEXT,font=('Segoe UI Semibold',10)); self.style.configure('TButton',background=BLUE,foreground='white',padding=(12,8),borderwidth=0); self.style.map('TButton',background=[('active','#4b96f3')]); self.style.configure('TCombobox',fieldbackground=PANEL2,background=PANEL2,foreground=TEXT)
        self.current='Dashboard'; self.build(); self.show_dashboard()
    def clear(self):
        for w in self.content.winfo_children(): w.destroy()
    def build(self):
        top=tk.Frame(self,bg='#080e19',height=68); top.pack(fill='x'); top.pack_propagate(False)
        self.logo_img=None
        if os.path.exists(LOGO):
            try: self.logo_img=tk.PhotoImage(file=LOGO); tk.Label(top,image=self.logo_img,bg='#080e19').pack(side='left',padx=(18,8))
            except: pass
        tk.Label(top,text=self.db.setting('company_name','PAYROLLPRO'),font=('Segoe UI Black',20),fg='white',bg='#080e19').pack(side='left',padx=10)
        tk.Label(top,text='• Sri Lanka HR & Payroll',font=('Segoe UI',10),fg=MUTED,bg='#080e19').pack(side='left')
        self.clock=tk.Label(top,fg=MUTED,bg='#080e19'); self.clock.pack(side='right',padx=24); self.tick()
        nav=tk.Frame(self,bg=NAVY,width=235); nav.pack(side='left',fill='y'); nav.pack_propagate(False)
        self.content=tk.Frame(self,bg=NAVY); self.content.pack(side='right',fill='both',expand=True,padx=18,pady=18)
        items=[('⌂','Dashboard'),('👥','Employees'),('🕒','Attendance'),('💰','Payroll'),('▣','Payslips'),('▤','Reports'),('⚙','Settings')]
        for icon,name in items:
            tk.Button(nav,text=f'{icon}   {name}',anchor='w',font=('Segoe UI',11),bd=0,fg=TEXT,bg=NAVY,activebackground=PANEL2,activeforeground='white',padx=20,pady=13,command=lambda n=name:self.go(n)).pack(fill='x')
        tk.Label(nav,text='DESKTOP • OFFLINE READY',fg='#58708f',bg=NAVY,font=('Segoe UI',8,'bold')).pack(side='bottom',pady=20)
    def tick(self): self.clock.config(text=datetime.now().strftime('%d %b %Y   %I:%M:%S %p')); self.after(1000,self.tick)
    def go(self,n): self.current=n; getattr(self,'show_'+n.lower())()
    def page_title(self,t,sub=''):
        tk.Label(self.content,text=t,font=('Segoe UI Semibold',24),fg='white',bg=NAVY).pack(anchor='w'); tk.Label(self.content,text=sub,fg=MUTED,bg=NAVY).pack(anchor='w',pady=(2,18) if sub else (0,18))
    def card(self,parent,label,value,accent=BLUE):
        f=tk.Frame(parent,bg=PANEL,highlightbackground=BORDER,highlightthickness=1); f.pack(side='left',fill='both',expand=True,padx=5); tk.Frame(f,bg=accent,width=4).pack(side='left',fill='y'); tk.Label(f,text=label.upper(),fg=MUTED,bg=PANEL,font=('Segoe UI',9,'bold')).pack(anchor='w',padx=18,pady=(15,4)); tk.Label(f,text=value,fg='white',bg=PANEL,font=('Segoe UI Semibold',21)).pack(anchor='w',padx=18,pady=(0,15)); return f
    def tree(self,parent,cols,widths):
        t=ttk.Treeview(parent,columns=cols,show='headings');
        for c,w in zip(cols,widths): t.heading(c,text=c); t.column(c,width=w,anchor='w')
        y=ttk.Scrollbar(parent,orient='vertical',command=t.yview); t.configure(yscrollcommand=y.set); t.pack(side='left',fill='both',expand=True); y.pack(side='right',fill='y'); return t
    def show_dashboard(self):
        self.clear(); self.page_title('Dashboard','Payroll control centre • local database • company-branded')
        month=date.today().strftime('%Y-%m'); today=date.today().isoformat(); emps=self.db.q("SELECT COUNT(*) n FROM employees WHERE status='Active'",one=True)['n']; present=self.db.q("SELECT COUNT(*) n FROM attendance WHERE work_date=? AND status='Present'",(today,),one=True)['n']; p=self.db.q('SELECT COALESCE(SUM(net),0) n FROM payroll WHERE month=?',(month,),one=True)['n']; epf=self.db.q('SELECT COALESCE(SUM(epf),0) n FROM payroll WHERE month=?',(month,),one=True)['n']; etf=self.db.q('SELECT COALESCE(SUM(etf),0) n FROM payroll WHERE month=?',(month,),one=True)['n']
        row=tk.Frame(self.content,bg=NAVY); row.pack(fill='x',pady=(0,14)); self.card(row,'Active Employees',str(emps)); self.card(row,'Present Today',str(present),GREEN); self.card(row,'Net Payroll',f'Rs. {p:,.2f}',BLUE); self.card(row,'EPF Employee',f'Rs. {epf:,.2f}',RED); self.card(row,'ETF Employer',f'Rs. {etf:,.2f}',GOLD)
        box=tk.Frame(self.content,bg=PANEL,highlightbackground=BORDER,highlightthickness=1); box.pack(fill='both',expand=True); tk.Label(box,text='Monthly Summary',font=('Segoe UI Semibold',16),fg='white',bg=PANEL).pack(anchor='w',padx=22,pady=18)
        gross=self.db.q('SELECT COALESCE(SUM(gross),0) n FROM payroll WHERE month=?',(month,),one=True)['n']; emp_epf=epf; emp_etf=etf; no_pay=self.db.q('SELECT COALESCE(SUM(no_pay),0) n FROM payroll WHERE month=?',(month,),one=True)['n']; deductions=self.db.q('SELECT COALESCE(SUM(deductions),0) n FROM payroll WHERE month=?',(month,),one=True)['n']
        for lab,val,acc in [('Gross Payroll',gross,BLUE),('EPF Employee 8%',emp_epf,RED),('EPF Employer 12%',gross*.12,GOLD),('ETF Employer 3%',emp_etf,GOLD),('No Pay',no_pay,RED),('Other Deductions',deductions,RED)]:
            f=tk.Frame(box,bg=PANEL2); f.pack(fill='x',padx=22,pady=4); tk.Label(f,text=lab,fg=MUTED,bg=PANEL2).pack(side='left',padx=14,pady=10); tk.Label(f,text=f'Rs. {val:,.2f}',fg='white',bg=PANEL2,font=('Segoe UI Semibold',11)).pack(side='right',padx=14)
    def show_employees(self):
        self.clear(); self.page_title('Employees','Employee master data, EPF number, bank details and salary')
        bar=tk.Frame(self.content,bg=NAVY); bar.pack(fill='x',pady=(0,12)); tk.Button(bar,text='＋ Add Employee',command=self.add_employee).pack(side='left'); tk.Button(bar,text='Edit Selected',command=self.edit_employee).pack(side='left',padx=8); tk.Button(bar,text='Deactivate',command=self.deactivate_employee).pack(side='left');
        self.emp_tree=self.tree(self.content,('ID','Employee No','Name','NIC','Branch','Department','Designation','Basic','EPF No','Status'),[45,100,180,115,120,120,130,100,100,80]); self.refresh_employees()
    def refresh_employees(self):
        for x in self.emp_tree.get_children(): self.emp_tree.delete(x)
        for r in self.db.q('SELECT id,emp_no,name,nic,branch,department,designation,basic,epf_no,status FROM employees ORDER BY emp_no'): self.emp_tree.insert('','end',iid=str(r['id']),values=(r['id'],r['emp_no'],r['name'],r['nic'] or '',r['branch'] or '',r['department'] or '',r['designation'] or '',f"{r['basic']:,.2f}",r['epf_no'] or '',r['status']))
    def employee_form(self,existing=None):
        win=tk.Toplevel(self); win.title('Employee'); win.geometry('700x650'); win.configure(bg=NAVY); win.grab_set(); tk.Label(win,text='Employee Details',font=('Segoe UI Semibold',20),fg='white',bg=NAVY).pack(anchor='w',padx=28,pady=22)
        fields=[('Employee No','emp_no'),('Full Name','name'),('NIC','nic'),('Phone','phone'),('Branch','branch'),('Department','department'),('Designation','designation'),('Joined Date','joined'),('Basic Salary','basic'),('Bank','bank'),('Account No','account'),('EPF No','epf_no')]; vars={}; form=tk.Frame(win,bg=NAVY); form.pack(fill='both',padx=28)
        for i,(lab,key) in enumerate(fields):
            rr=i//2; cc=(i%2)*2; tk.Label(form,text=lab,fg=MUTED,bg=NAVY).grid(row=rr,column=cc,sticky='w',padx=(0,10),pady=(8,2)); v=tk.StringVar(value=str(existing[key] if existing and existing[key] is not None else '')); vars[key]=v; tk.Entry(form,textvariable=v,bg=PANEL2,fg=TEXT,insertbackground='white',relief='flat',width=28).grid(row=rr,column=cc+1,sticky='ew',pady=(8,2),ipady=7)
        def save():
            if not vars['emp_no'].get() or not vars['name'].get(): messagebox.showwarning('Required','Employee No and Name are required.'); return
            try: basic=float(vars['basic'].get() or 0)
            except: messagebox.showerror('Error','Basic salary must be a number.'); return
            vals=[vars[k].get() for _,k in fields]; vals[8]=basic
            try:
                if existing: self.db.q('UPDATE employees SET emp_no=?,name=?,nic=?,phone=?,branch=?,department=?,designation=?,joined=?,basic=?,bank=?,account=?,epf_no=? WHERE id=?',(*vals,existing['id']))
                else: self.db.q('INSERT INTO employees(emp_no,name,nic,phone,branch,department,designation,joined,basic,bank,account,epf_no) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',vals)
            except sqlite3.IntegrityError: messagebox.showerror('Duplicate','Employee No already exists.'); return
            win.destroy(); self.refresh_employees()
        tk.Button(win,text='Save Employee',command=save,bg=BLUE,fg='white',bd=0,padx=24,pady=11).pack(anchor='e',padx=28,pady=22)
    def add_employee(self): self.employee_form()
    def edit_employee(self):
        s=self.emp_tree.selection();
        if not s:return
        r=self.db.q('SELECT * FROM employees WHERE id=?',(int(s[0]),),one=True); self.employee_form(r)
    def deactivate_employee(self):
        s=self.emp_tree.selection();
        if s and messagebox.askyesno('Deactivate','Deactivate selected employee?'): self.db.q("UPDATE employees SET status='Inactive' WHERE id=?",(int(s[0]),)); self.refresh_employees()
    def show_attendance(self):
        self.clear(); self.page_title('Attendance','Manual attendance, corrections, OT and leave • biometric import-ready')
        bar=tk.Frame(self.content,bg=NAVY); bar.pack(fill='x',pady=(0,12)); tk.Button(bar,text='＋ Add / Correct Attendance',command=self.add_attendance).pack(side='left'); tk.Button(bar,text='Delete Selected',command=self.delete_attendance).pack(side='left',padx=8)
        self.att_tree=self.tree(self.content,('ID','Date','Employee','IN','OUT','Status','OT Hrs','Note'),[55,105,190,90,90,100,80,250]); self.refresh_attendance()
    def refresh_attendance(self):
        for x in self.att_tree.get_children(): self.att_tree.delete(x)
        for r in self.db.q('SELECT a.*,e.emp_no,e.name FROM attendance a JOIN employees e ON e.id=a.emp_id ORDER BY work_date DESC,id DESC'): self.att_tree.insert('','end',iid=str(r['id']),values=(r['id'],r['work_date'],f"{r['emp_no']} - {r['name']}",r['time_in'] or '',r['time_out'] or '',r['status'],r['ot_hours'],r['note'] or ''))
    def add_attendance(self):
        win=tk.Toplevel(self); win.title('Attendance Entry / Correction'); win.geometry('590x500'); win.configure(bg=NAVY); win.grab_set(); tk.Label(win,text='Attendance Entry / Correction',font=('Segoe UI Semibold',20),fg='white',bg=NAVY).pack(anchor='w',padx=28,pady=20)
        emps=self.db.q("SELECT id,emp_no,name FROM employees WHERE status='Active' ORDER BY emp_no"); labels=[f"{r['id']}|{r['emp_no']} - {r['name']}" for r in emps]; vals={}
        def row(lab,typ,values=None):
            f=tk.Frame(win,bg=NAVY); f.pack(fill='x',padx=28,pady=6); tk.Label(f,text=lab,width=15,anchor='w',fg=MUTED,bg=NAVY).pack(side='left'); w=ttk.Combobox(f,values=values,state='readonly',width=40) if typ=='combo' else tk.Entry(f,bg=PANEL2,fg=TEXT,insertbackground='white',relief='flat',width=42); w.pack(side='left',ipady=6); vals[lab]=w
        row('Employee','combo',labels); row('Date','entry'); row('Time In','entry'); row('Time Out','entry'); row('Status','combo',['Present','Absent','Leave','Holiday']); row('OT Hours','entry'); row('Note','entry'); vals['Date'].insert(0,date.today().isoformat()); vals['Status'].set('Present')
        def save():
            try:eid=int(vals['Employee'].get().split('|')[0]); ot=float(vals['OT Hours'].get() or 0)
            except: messagebox.showerror('Error','Select employee and enter valid OT hours.'); return
            self.db.q('''INSERT INTO attendance(emp_id,work_date,time_in,time_out,status,ot_hours,note) VALUES(?,?,?,?,?,?,?) ON CONFLICT(emp_id,work_date) DO UPDATE SET time_in=excluded.time_in,time_out=excluded.time_out,status=excluded.status,ot_hours=excluded.ot_hours,note=excluded.note''',(eid,vals['Date'].get(),vals['Time In'].get(),vals['Time Out'].get(),vals['Status'].get(),ot,vals['Note'].get())); win.destroy(); self.refresh_attendance()
        tk.Button(win,text='Save / Correct',command=save,bg=BLUE,fg='white',bd=0,padx=22,pady=11).pack(anchor='e',padx=28,pady=20)
    def delete_attendance(self):
        s=self.att_tree.selection();
        if s and messagebox.askyesno('Delete','Delete selected attendance record?'): self.db.q('DELETE FROM attendance WHERE id=?',(int(s[0]),)); self.refresh_attendance()
    def show_payroll(self):
        self.clear(); self.page_title('Payroll','Monthly salary engine • configurable earnings & deductions • EPF/ETF')
        top=tk.Frame(self.content,bg=NAVY); top.pack(fill='x',pady=(0,10)); tk.Label(top,text='Payroll Month',fg=MUTED,bg=NAVY).pack(side='left'); month=tk.StringVar(value=date.today().strftime('%Y-%m')); tk.Entry(top,textvariable=month,bg=PANEL2,fg=TEXT,insertbackground='white',relief='flat',width=12).pack(side='left',padx=8,ipady=7); tk.Button(top,text='Calculate / Update',command=lambda:self.calculate_payroll(month.get())).pack(side='left'); tk.Button(top,text='Manage Pay Items',command=lambda:self.pay_items(month.get())).pack(side='left',padx=8); tk.Button(top,text='Export CSV',command=self.export_payroll).pack(side='left')
        self.pay_tree=self.tree(self.content,('Employee','Basic','Allowances','OT','Gross','EPF 8%','No Pay','Deductions','Net','EPF 12%','ETF 3%'),[180,85,90,75,95,90,90,100,100,95,85]); self.refresh_payroll(month.get())
    def pay_items(self,month):
        win=tk.Toplevel(self); win.title('Salary Categories / Pay Items'); win.geometry('720x560'); win.configure(bg=NAVY); win.grab_set(); tk.Label(win,text='Salary Categories',font=('Segoe UI Semibold',20),fg='white',bg=NAVY).pack(anchor='w',padx=24,pady=18); tk.Label(win,text='Examples: Attendance Allowance, Meal, Bonus, Advance, Loan, Shortage, Other Deduction',fg=MUTED,bg=NAVY).pack(anchor='w',padx=24)
        emps=self.db.q("SELECT id,emp_no,name FROM employees WHERE status='Active' ORDER BY emp_no"); labels=[f"{r['id']}|{r['emp_no']} - {r['name']}" for r in emps]; form=tk.Frame(win,bg=NAVY); form.pack(fill='x',padx=24,pady=15); vs={}
        for i,(lab,typ,values) in enumerate([('Employee','combo',labels),('Category','entry',None),('Type','combo',['Earning','Deduction']),('Amount','entry',None),('Note','entry',None)]):
            tk.Label(form,text=lab,fg=MUTED,bg=NAVY).grid(row=i,column=0,sticky='w',pady=5); w=ttk.Combobox(form,values=values,state='readonly',width=45) if typ=='combo' else tk.Entry(form,bg=PANEL2,fg=TEXT,insertbackground='white',relief='flat',width=47); w.grid(row=i,column=1,pady=5,ipady=6); vs[lab]=w
        def add():
            try:eid=int(vs['Employee'].get().split('|')[0]); amt=float(vs['Amount'].get())
            except: messagebox.showerror('Error','Select employee and enter amount.'); return
            if not vs['Category'].get(): messagebox.showerror('Error','Enter a category.'); return
            self.db.q('INSERT INTO pay_items(emp_id,month,category,item_type,amount,note) VALUES(?,?,?,?,?,?)',(eid,month,vs['Category'].get(),vs['Type'].get(),amt,vs['Note'].get())); refresh()
        tk.Button(win,text='＋ Add Item',command=add).pack(anchor='e',padx=24,pady=8)
        t=self.tree(win,('Employee','Category','Type','Amount','Note'),[180,180,100,100,160]); t.pack(fill='both',expand=True,padx=24,pady=10)
        def refresh():
            for x in t.get_children():t.delete(x)
            for r in self.db.q('SELECT p.*,e.emp_no,e.name FROM pay_items p JOIN employees e ON e.id=p.emp_id WHERE p.month=? ORDER BY e.emp_no,p.id',(month,)): t.insert('','end',iid=str(r['id']),values=(f"{r['emp_no']} - {r['name']}",r['category'],r['item_type'],f"{r['amount']:,.2f}",r['note'] or ''))
        def delete():
            s=t.selection();
            if s:self.db.q('DELETE FROM pay_items WHERE id=?',(int(s[0]),)); refresh()
        tk.Button(win,text='Delete Selected',command=delete,bg=RED).pack(anchor='e',padx=24,pady=(0,18)); refresh()
    def calculate_payroll(self,month):
        try: y,m=map(int,month.split('-')); days=calendar.monthrange(y,m)[1]
        except: messagebox.showerror('Month','Use YYYY-MM, e.g. 2026-10'); return
        for e in self.db.q("SELECT * FROM employees WHERE status='Active'"):
            att=self.db.q('SELECT * FROM attendance WHERE emp_id=? AND work_date LIKE ?',(e['id'],month+'-%')); absent=sum(1 for a in att if a['status']=='Absent'); ot=sum(float(a['ot_hours'] or 0) for a in att); hourly=(e['basic']/days/8) if days else 0; otpay=ot*hourly*1.5; nopay=e['basic']/days*absent
            items=self.db.q('SELECT * FROM pay_items WHERE emp_id=? AND month=?',(e['id'],month)); allowances=sum(r['amount'] for r in items if r['item_type']=='Earning'); deductions=sum(r['amount'] for r in items if r['item_type']=='Deduction'); gross=max(0,e['basic']-nopay+otpay+allowances); epf=gross*.08; net=gross-epf-deductions; etf=gross*.03
            self.db.q('''INSERT INTO payroll(emp_id,month,basic,allowances,ot,gross,epf,no_pay,deductions,net,etf,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(emp_id,month) DO UPDATE SET basic=excluded.basic,allowances=excluded.allowances,ot=excluded.ot,gross=excluded.gross,epf=excluded.epf,no_pay=excluded.no_pay,deductions=excluded.deductions,net=excluded.net,etf=excluded.etf,created=excluded.created''',(e['id'],month,e['basic'],allowances,otpay,gross,epf,nopay,deductions,net,etf,datetime.now().isoformat()))
        self.refresh_payroll(month); messagebox.showinfo('Payroll','Payroll calculated successfully.')
    def refresh_payroll(self,month):
        for x in self.pay_tree.get_children():self.pay_tree.delete(x)
        for r in self.db.q('SELECT p.*,e.emp_no,e.name FROM payroll p JOIN employees e ON e.id=p.emp_id WHERE month=? ORDER BY e.emp_no',(month,)): self.pay_tree.insert('','end',values=(f"{r['emp_no']} - {r['name']}",*[f"{r[k]:,.2f}" for k in ['basic','allowances','ot','gross','epf','no_pay','deductions','net']],f"{r['gross']*.12:,.2f}",f"{r['etf']:,.2f}"))
    def export_payroll(self):
        path=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')]);
        if not path:return
        rows=self.db.q('SELECT p.*,e.emp_no,e.name FROM payroll p JOIN employees e ON e.id=p.emp_id ORDER BY month,e.emp_no')
        with open(path,'w',newline='',encoding='utf-8-sig') as f:
            w=csv.writer(f); w.writerow(['Employee No','Name','Month','Basic','Allowances','OT','Gross','EPF Employee 8%','No Pay','Other Deductions','Net','EPF Employer 12%','ETF Employer 3%']); [w.writerow([r['emp_no'],r['name'],r['month'],r['basic'],r['allowances'],r['ot'],r['gross'],r['epf'],r['no_pay'],r['deductions'],r['net'],r['gross']*.12,r['etf']]) for r in rows]
        messagebox.showinfo('Exported',path)
    def show_payslips(self):
        self.clear(); self.page_title('Paysheets & Payslips','Company-branded printable salary sheets with separate EPF/ETF details')
        box=tk.Frame(self.content,bg=PANEL); box.pack(fill='x',pady=(0,14)); tk.Label(box,text='Month',fg=MUTED,bg=PANEL).pack(side='left',padx=16,pady=16); self.ps_month=tk.StringVar(value=date.today().strftime('%Y-%m')); tk.Entry(box,textvariable=self.ps_month,bg=PANEL2,fg=TEXT,insertbackground='white',relief='flat').pack(side='left',ipady=6); tk.Button(box,text='Generate Payslips',command=self.generate_payslips).pack(side='left',padx=12); tk.Button(box,text='Open Company Settings',command=self.show_settings).pack(side='left')
        tk.Label(self.content,text='The payslip includes company logo/name, employee details, earnings, deductions, EPF 8%, employer EPF 12%, ETF 3% and net salary.',fg=MUTED,bg=NAVY).pack(anchor='w',pady=10)
    def generate_payslips(self):
        month=self.ps_month.get(); folder=filedialog.askdirectory(title='Choose payslip folder');
        if not folder:return
        rows=self.db.q('SELECT p.*,e.* FROM payroll p JOIN employees e ON e.id=p.emp_id WHERE p.month=?',(month,))
        if not rows: messagebox.showwarning('No Payroll','Calculate payroll for this month first.'); return
        company=self.db.setting('company_name','PAYROLLPRO'); address=self.db.setting('company_address',''); phone=self.db.setting('company_phone',''); logo_url=('file:///'+LOGO.replace('\\','/')) if os.path.exists(LOGO) else ''
        for r in rows:
            fn=os.path.join(folder,f"Payslip_{r['emp_no']}_{month}.html"); logo=f'<img src="{logo_url}" style="height:65px;max-width:180px">' if logo_url else ''
            html=f'''<html><head><meta charset="utf-8"><title>{company} Payslip</title><style>body{{font-family:Arial;color:#111;padding:35px}}.head{{display:flex;justify-content:space-between;border-bottom:3px solid #17345f;padding-bottom:15px}}table{{border-collapse:collapse;width:100%;max-width:760px}}td{{padding:9px;border-bottom:1px solid #ddd}}.sec{{font-weight:bold;background:#eef3f9}}.net{{font-size:20px;font-weight:bold}}small{{color:#666}}</style></head><body><div class="head"><div>{logo}<h1>{company}</h1><div>{address}<br>{phone}</div></div><div><b>SALARY PAYSLIP</b><br>{month}</div></div><p><b>{r['emp_no']} — {r['name']}</b><br>{r['designation'] or ''} | {r['department'] or ''} | {r['branch'] or ''}<br>NIC: {r['nic'] or ''} &nbsp; EPF No: {r['epf_no'] or ''}</p><table><tr class="sec"><td>Earnings</td><td>Amount</td></tr><tr><td>Basic Salary</td><td>Rs. {r['basic']:,.2f}</td></tr><tr><td>Allowances</td><td>Rs. {r['allowances']:,.2f}</td></tr><tr><td>Overtime</td><td>Rs. {r['ot']:,.2f}</td></tr><tr><td>No Pay</td><td>- Rs. {r['no_pay']:,.2f}</td></tr><tr><td><b>Gross</b></td><td><b>Rs. {r['gross']:,.2f}</b></td></tr><tr class="sec"><td>Deductions</td><td>Amount</td></tr><tr><td>EPF Employee 8%</td><td>- Rs. {r['epf']:,.2f}</td></tr><tr><td>Other Deductions / Shortage / Loans</td><td>- Rs. {r['deductions']:,.2f}</td></tr><tr class="net"><td>NET SALARY</td><td>Rs. {r['net']:,.2f}</td></tr><tr class="sec"><td>Employer Contributions</td><td>Amount</td></tr><tr><td>EPF Employer 12%</td><td>Rs. {r['gross']*.12:,.2f}</td></tr><tr><td>ETF Employer 3%</td><td>Rs. {r['etf']:,.2f}</td></tr></table><p><small>Generated by {company} PayrollPro Desktop • Please retain this payslip for your records.</small></p></body></html>'''; open(fn,'w',encoding='utf-8').write(html)
        messagebox.showinfo('Done',f'{len(rows)} branded payslips created in:\n{folder}')
    def show_reports(self):
        self.clear(); self.page_title('Reports','Separate summaries for payroll, EPF, ETF, attendance and deductions'); month=date.today().strftime('%Y-%m'); tk.Label(self.content,text=f'Current month: {month}',fg=MUTED,bg=NAVY).pack(anchor='w')
        p=self.db.q('SELECT COALESCE(SUM(gross),0) gross,COALESCE(SUM(epf),0) epf,COALESCE(SUM(etf),0) etf,COALESCE(SUM(deductions),0) ded,COALESCE(SUM(no_pay),0) nopay,COALESCE(SUM(net),0) net FROM payroll WHERE month=?',(month,),one=True); gross=p['gross'];
        row=tk.Frame(self.content,bg=NAVY); row.pack(fill='x',pady=14); self.card(row,'Gross Payroll',f'Rs. {gross:,.2f}',BLUE); self.card(row,'EPF Employee 8%',f"Rs. {p['epf']:,.2f}",RED); self.card(row,'EPF Employer 12%',f'Rs. {gross*.12:,.2f}',GOLD); self.card(row,'ETF Employer 3%',f"Rs. {p['etf']:,.2f}",GOLD)
        row2=tk.Frame(self.content,bg=NAVY); row2.pack(fill='x',pady=0); self.card(row2,'Net Salary',f"Rs. {p['net']:,.2f}",GREEN); self.card(row2,'No Pay',f"Rs. {p['nopay']:,.2f}",RED); self.card(row2,'Other Deductions',f"Rs. {p['ded']:,.2f}",RED); self.card(row2,'Employer Total Cost',f"Rs. {gross+gross*.12+p['etf']:,.2f}",BLUE)
        box=tk.Frame(self.content,bg=PANEL); box.pack(fill='both',expand=True,pady=18); tk.Label(box,text='Separate report exports',font=('Segoe UI Semibold',15),fg='white',bg=PANEL).pack(anchor='w',padx=20,pady=18)
        for txt,typ in [('EPF Summary','epf'),('ETF Summary','etf'),('Salary Summary','salary'),('Deduction / Shortage / Loan Summary','deductions'),('Attendance Summary','attendance')]: tk.Button(box,text=txt,command=lambda t=typ:self.export_report(t,month),bg=PANEL2,fg=TEXT,bd=0,padx=16,pady=12).pack(side='left',padx=7,pady=8)
    def export_report(self,typ,month):
        path=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')],initialfile=f'{typ}_{month}.csv');
        if not path:return
        with open(path,'w',newline='',encoding='utf-8-sig') as f:
            w=csv.writer(f)
            if typ in ('epf','etf','salary','deductions'):
                rows=self.db.q('SELECT p.*,e.emp_no,e.name FROM payroll p JOIN employees e ON e.id=p.emp_id WHERE p.month=?',(month,)); w.writerow(['Employee No','Name','Month','Gross','EPF Employee 8%','EPF Employer 12%','ETF Employer 3%','No Pay','Other Deductions','Net'])
                for r in rows:w.writerow([r['emp_no'],r['name'],month,r['gross'],r['epf'],r['gross']*.12,r['etf'],r['no_pay'],r['deductions'],r['net']])
            else:
                w.writerow(['Date','Employee','IN','OUT','Status','OT Hours','Note']); rows=self.db.q('SELECT a.*,e.emp_no,e.name FROM attendance a JOIN employees e ON e.id=a.emp_id WHERE a.work_date LIKE ?',(month+'-%',)); [w.writerow([r['work_date'],f"{r['emp_no']} - {r['name']}",r['time_in'],r['time_out'],r['status'],r['ot_hours'],r['note']]) for r in rows]
        messagebox.showinfo('Exported',path)
    def show_settings(self):
        self.clear(); self.page_title('Settings','Company branding, payroll defaults, logo and database backup')
        box=tk.Frame(self.content,bg=PANEL,highlightbackground=BORDER,highlightthickness=1); box.pack(fill='x',pady=8); tk.Label(box,text='Company Profile',font=('Segoe UI Semibold',16),fg='white',bg=PANEL).pack(anchor='w',padx=22,pady=18)
        vars={}
        for i,(lab,key) in enumerate([('Company Name','company_name'),('Address','company_address'),('Phone / Email','company_phone')]):
            tk.Label(box,text=lab,fg=MUTED,bg=PANEL).pack(anchor='w',padx=22); v=tk.StringVar(value=self.db.setting(key,'')); vars[key]=v; tk.Entry(box,textvariable=v,bg=PANEL2,fg=TEXT,insertbackground='white',relief='flat').pack(fill='x',padx=22,pady=(3,10),ipady=7)
        def save_profile():
            for k,v in vars.items():self.db.set_setting(k,v.get())
            self.build(); self.show_settings(); messagebox.showinfo('Saved','Company profile saved.')
        tk.Button(box,text='Save Company Profile',command=save_profile).pack(anchor='e',padx=22,pady=12)
        lb=tk.Frame(self.content,bg=PANEL); lb.pack(fill='x',pady=10); tk.Label(lb,text='Company Logo',font=('Segoe UI Semibold',15),fg='white',bg=PANEL).pack(anchor='w',padx=22,pady=16); tk.Label(lb,text='PNG recommended. The same logo is used in the app header and payslips.',fg=MUTED,bg=PANEL).pack(anchor='w',padx=22)
        tk.Button(lb,text='Choose / Replace Logo',command=self.choose_logo).pack(anchor='w',padx=22,pady=14)
        dbx=tk.Frame(self.content,bg=PANEL); dbx.pack(fill='x',pady=10); tk.Label(dbx,text='Data & Backup',font=('Segoe UI Semibold',15),fg='white',bg=PANEL).pack(anchor='w',padx=22,pady=16); tk.Button(dbx,text='Backup Database',command=self.backup).pack(anchor='w',padx=22,pady=8); tk.Button(dbx,text='Open Data Folder',command=lambda:os.startfile(APP_DIR) if os.name=='nt' else messagebox.showinfo('Folder',APP_DIR)).pack(anchor='w',padx=22,pady=8); tk.Label(dbx,text='Payroll defaults: EPF Employee 8% • EPF Employer 12% • ETF Employer 3%',fg=MUTED,bg=PANEL).pack(anchor='w',padx=22,pady=14)
    def choose_logo(self):
        p=filedialog.askopenfilename(filetypes=[('PNG image','*.png')]);
        if p:
            try: shutil.copy2(p,LOGO); self.build(); self.show_settings(); messagebox.showinfo('Logo','Company logo updated.')
            except Exception as e: messagebox.showerror('Logo Error',str(e))
    def backup(self):
        path=filedialog.asksaveasfilename(defaultextension='.db',filetypes=[('Database','*.db')],initialfile=f'PayrollPro_Backup_{date.today().isoformat()}.db');
        if path: shutil.copy2(DB,path); messagebox.showinfo('Backup','Database backup created.')

if __name__=='__main__': App().mainloop()
