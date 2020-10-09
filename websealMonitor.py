import requests
import asyncio
import aiohttp
import time
import operator
import sqlite3
from datetime import datetime
from tkinter import *
from tkinter import ttk
import tkinter as tk

window = Tk()
window.title("Simple ISAM Junction Monitoring")
width  = window.winfo_screenwidth()
height = window.winfo_screenheight()
window.geometry(f'{width}x{height}')
window.grid_columnconfigure(0, weight=1)
window.grid_rowconfigure(1,weight=1)
#------Create Frame-----
main_frame = Frame(window)
main_frame.grid(column=0,row=1,sticky='nsew', rowspan=2)

appliance_frame = Frame(window)
appliance_frame.grid(column=0,row=0, sticky=W, pady=(5,5))

Label(appliance_frame, text= "ADD SERVER").grid(column=0, row=0, columnspan=3, pady=5, padx = 10)
Label(appliance_frame, text= "Appliance IP").grid(column=0, row=1, pady=3, sticky=W,padx = 10)
Label(appliance_frame, text= "Appliance User").grid(column=0, row=2, pady=3, sticky=W,padx = 10)
Label(appliance_frame, text= "Appliance Password").grid(column=0, row=3, pady=3, sticky=W,padx = 10)

app_ip_entry = Entry(appliance_frame, width=50)
user_entry = Entry(appliance_frame, width=50)
pass_entry = Entry(appliance_frame, width=50)

app_ip_entry.grid(column=1, row=1, columnspan=2, padx=(0,20))
user_entry.grid(column=1, row=2, columnspan=2, padx=(0,20))
pass_entry.grid(column=1, row=3, columnspan=2, padx=(0,20))


#------Create Canvas------
data_canvas = Canvas(main_frame)


#-------Create ScrollBar-----
scroll_bar_y = ttk.Scrollbar(main_frame, orient=VERTICAL, command=data_canvas.yview)
scroll_bar = ttk.Scrollbar(main_frame, orient=HORIZONTAL, command=data_canvas.xview)
scroll_bar_y.pack(side=RIGHT, fill=Y,anchor='n')
data_canvas.pack(fill=BOTH, expand=True)
scroll_bar.pack(fill=X)
data_canvas.configure(xscrollcommand=scroll_bar.set,yscrollcommand=scroll_bar_y.set)
data_canvas.bind('<Configure>', lambda e: data_canvas.configure(scrollregion = data_canvas.bbox('all')))

#-------Create another Frame-----
second_frame = Frame(data_canvas)
data_canvas.create_window((0,0), window=second_frame,anchor='nw')

# "10.204.149.14","10.204.149.15","10.204.149.16","10.204.149.17","10.204.149.19"
api_rp = []
api_rp_urls = []
aac = []
aac_checkboxes=[]
complete_data = []
app_checkboxes=[]
sleep_time = 1


# -------Create Server Class-----
class Server:
    def __init__(self, server_uuid, server_state,operation_state,server_hostname,server_port,http_port,virtual_junction_hostname,current_requests,total_requests):
        self.server_uuid = server_uuid
        self.server_state = server_state
        self.operation_state = operation_state
        self.server_hostname = server_hostname
        self.server_port = server_port
        self.http_port = http_port
        self.virtual_junction_hostname = virtual_junction_hostname
        self.current_requests = current_requests
        self.total_requests = total_requests

class HostServer:
    def __init__(self, hostname, server):
        self.hostname = hostname
        self.server = server

def getCheckedBoxes():
    conn = sqlite3.connect('app_database.db')
    c = conn.cursor()
    temp = []
    for i in range(len(app_checkboxes)):
        if(app_checkboxes[i].get()==1):
            temp.append(i)
    for i in range(len(temp)):
        item = api_rp[0][temp[i]]
        c.execute("DELETE FROM appliances WHERE hostname = '" + item +"'")
        conn.commit()
     
    conn.close()
    
    checkDatabase()
    updateUI()
    # print(item)

def checkDatabase():
    api_rp.clear()
    conn = sqlite3.connect('app_database.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS appliances (hostname text,username text,password text)")
    c.execute("CREATE TABLE IF NOT EXISTS aac_appliances (hostname text,username text,password text)")
    c.execute("SELECT *, oid FROM appliances")
    records = c.fetchall()

    if(len(records)>0):
        api_rp.clear()
        for record in records:
            api_rp.append(record)

    c.execute("SELECT *, oid FROM aac_appliances")
    records = c.fetchall()
    if(len(records)>0):
        aac.clear()
        for record in records:
            aac.append(record)

    conn.commit()    
    conn.close()
    print(api_rp)
    print(aac)
    runningOnce()

def addData():
    #--Check Option--
    if rpVar.get()==1 and aacVar.get()==1:
        print("Choose One")
    elif rpVar.get()==0 and aacVar.get()==0:
        print("Choose One")
    elif rpVar.get()==1 and aacVar.get()==0:
        table = "appliances"
    elif rpVar.get()==0 and aacVar.get()==1:
        table = "aac_appliances"
    print(table)
    # Test Connection First
    try:    
        url = 'https://'+str(app_ip_entry.get())
        r = requests.get(url, auth=(str(user_entry.get()),str(pass_entry.get())), headers = {'Content-Type': 'application/json; odata=verbose', 'Accept':'application/json; odata=verbose'}, verify=False, timeout=2)
        if(r.status_code == 200):
            conn = sqlite3.connect('app_database.db')
            c = conn.cursor()

            #-----Check if the content is exist-----
            c.execute("SELECT * FROM "+ table +" WHERE hostname = '" + str(app_ip_entry.get()) +"'")
            records = c.fetchall()
            if(len(records)>0):
                print("Server is already Exist")
            else:
                c.execute("INSERT INTO "+ table +" VALUES (:hostname,:username,:password)",
                {
                    'hostname':app_ip_entry.get(), 
                    'username':user_entry.get(),
                    'password':pass_entry.get(),
                })
                
                app_ip_entry.delete(0,END)
                user_entry.delete(0,END)
                pass_entry.delete(0,END)

            conn.commit()
            conn.close()            
        else:
            print("Not Accesible")
    except requests.exceptions.RequestException as e:
        print(str(e))

    checkDatabase()

def updateAPIURL():
    api_rp_urls.clear()
    for i in range(len(api_rp)):
        item = api_rp[i]
        url = "https://" + item[0] + "/wga/reverseproxy/api_rp/junctions?junctions_id=/mga"
        itemset = (url, item[1], item[2])
        if url not in api_rp_urls:
            api_rp_urls.append(itemset)
        
def sortFunc(e):
    return e['server_hostname']
# -------Get Servers Total-----
def parseData(server_data):
    temp_index = 0
    total_servers = 1
    servers = []
    while True:
        result = server_data.find('#',temp_index)
        if result!= -1:
            servers.append(server_data[temp_index:result])
            total_servers = total_servers+1
            temp_index = result+1
        else:
            servers.append(server_data[temp_index:])
            break

    start_index = 0
    end_index = 0
    servers_object = []
    for i in range(total_servers):

        # --------Start Parsing on each servers-------
        temp_string = servers[i]
        start_index = temp_string.find('server_uuid')
        resp_index = temp_string.find('!',start_index)
        end_index = temp_string.find(';',start_index)

        server_uuid = temp_string[resp_index+1:end_index]

        start_index = temp_string.find('server_state')
        resp_index = temp_string.find('!',start_index)
        end_index = temp_string.find(';',start_index)

        server_state = temp_string[resp_index+1:end_index]

        start_index = temp_string.find('operation_state')
        resp_index = temp_string.find('!',start_index)
        end_index = temp_string.find(';',start_index)

        operation_state = temp_string[resp_index+1:end_index]

        start_index = temp_string.find('server_hostname')
        resp_index = temp_string.find('!',start_index)
        end_index = temp_string.find(';',start_index)

        server_hostname = temp_string[resp_index+1:end_index]

        start_index = temp_string.find('server_port')
        resp_index = temp_string.find('!',start_index)
        end_index = temp_string.find(';',start_index)

        server_port = temp_string[resp_index+1:end_index]

        start_index = temp_string.find('http_port')
        resp_index = temp_string.find('!',start_index)
        end_index = temp_string.find(';',start_index)

        http_port = temp_string[resp_index+1:end_index]

        start_index = temp_string.find('virtual_junction_hostname')
        resp_index = temp_string.find('!',start_index)
        end_index = temp_string.find(';',start_index)

        virtual_junction_hostname = temp_string[resp_index+1:end_index]

        start_index = temp_string.find('current_requests')
        resp_index = temp_string.find('!',start_index)
        end_index = temp_string.find(';',start_index)

        current_requests = temp_string[resp_index+1:end_index]

        start_index = temp_string.find('total_requests')
        resp_index = temp_string.find('!',start_index)
        end_index = temp_string.find(';',start_index)

        total_requests = temp_string[resp_index+1:end_index]

        server_object = Server(server_uuid,server_state,operation_state,server_hostname,server_port,http_port,virtual_junction_hostname,current_requests,total_requests)
        servers_object.append(server_object)    
    
    if(len(servers_object) > 0):
        servers_object.sort(key=operator.attrgetter('server_hostname'))
    return servers_object

#--------Create Async Call Function------
async def get(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url = url[0], headers = {'content-type': 'application/json; odata=verbose', 'accept':'application/json; odata=verbose'},auth = aiohttp.BasicAuth(url[1], url[2]),ssl=False) as response:
                resp = await response.json()
                server_data_raw = resp['servers']

                #-----Create HostServer and Store it------
                servers_object = parseData(server_data_raw)
                slash_index = url[0].find('/',8)
                hostname = url[0][8:slash_index]
                complete_data.append(HostServer(hostname, servers_object))

    except Exception as e:
        print("Unable to retrive data because of" + str(e))

async def main(urls):
    complete_data.clear()
    ret = await asyncio.gather(*[get(url) for url in urls])

def runningLoop(sleeptime):
    complete_data.clear()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(api_rp_urls))

    print("Waiting for 1 second")
    time.sleep(sleeptime)

def runningOnce():
    complete_data.clear()
    updateAPIURL()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(api_rp_urls))
    updateUI()

def addServertoMonitor():
    app = str(server_add.get())
    if app!= "":
        api_rp.append(app)
    runningOnce()
    server_add.delete(0,END)

def updateUI():
    complete_data.sort(key=operator.attrgetter('hostname'))
    aac.sort(key=lambda tup: tup[0])
    col = 3
    row = 1
    span = 1
    span2 = 1
    for i in range(len(complete_data)):
        app = complete_data[i]
        app_ip = Label(second_frame, text="Appliance IP : "+app.hostname, borderwidth=2, relief="solid")
        backend_server_txt = Label(second_frame, text="Backend Servers: /mga")

        app_ip.grid(row=1, column=i, padx=(10,10))
        backend_server_txt.grid(row=2, column=i,padx=(10,10))
        
        var = IntVar()
        Checkbutton(appliance_frame, text = f'{app.hostname}', variable=var).grid(column = col, row = row, sticky=W)
        app_checkboxes.append(var)

        if(i%3==2 and i!=0):
            span = span+1
            col=col+1
            row = 1
        else:
            row = row+1
        datacol = 3
        for x in range(len(app.server)):
            server_object = app.server[x]
            Label(second_frame, padx = 15, pady = 10, borderwidth=2, relief="groove", text = server_object.server_hostname + ":" + server_object.server_port).grid(row=datacol, column=i,padx=(10,10))
            if(server_object.server_state=="running"):
                color1 = "green"
            else:
                color1 = "red"

            if(server_object.operation_state=="Online"):
                color2 = "green"
            else:
                color2 = "red"
            Label(second_frame, text = "Server State : " + server_object.server_state, fg=color1, font=(None, 8)).grid(row=datacol+1, column=i,padx=(10,10))
            Label(second_frame, text = " Operational State : " + server_object.operation_state, fg=color2, font=(None, 8)).grid(row=datacol+2, column=i,padx=(10,10))
            datacol = datacol + 3
    temp_col = col+1
    starting = col +1
    row = 1
    for i in range(len(aac)):
        var = IntVar()
        Checkbutton(appliance_frame, text = f'{aac[i][0]}', variable=var).grid(column = temp_col, row = row, sticky=W)
        aac_checkboxes.append(var)

        if(i%3==2 and i!=0):
            temp_col=temp_col+1
            row = 1
            span2 = span2 +1
        else:
            row = row+1
    Label(appliance_frame, text="MANAGE RP APPLIANCES").grid(column = 3, row=0, columnspan = span)
    Label(appliance_frame, text="MANAGE AAC APPLIANCES").grid(column = starting, row=0, columnspan=span2)
    Label(appliance_frame,justify=LEFT, text = "Last Update : " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"), font=(None,8)).grid(row=5, column=0,sticky = W, padx=10)
    Button(appliance_frame, text="Restart Runtime").grid(column=starting, row=4, sticky=W,columnspan=span2)
    Button(appliance_frame, text="Reload Runtime").grid(column=starting+1, row=4, sticky=W,padx=(0,0), columnspan=span2)

rpVar = IntVar()
aacVar = IntVar()

Button(appliance_frame, text="Delete Server", command=getCheckedBoxes).grid(column=3, row=4, sticky=W)
Button(appliance_frame, text="Add Server", command=addData).grid(column=2, row=4, sticky=E,padx=(25,20))

Checkbutton(appliance_frame, text = "RP", var=rpVar).grid(column=1, row=4, sticky=W)
Checkbutton(appliance_frame, text = "AAC", var=aacVar).grid(column=1, row=4, sticky=W, padx=(50,0))
Button(appliance_frame, text="Refresh", command=runningOnce).grid(column=1, row=5, sticky=W,padx=(0,20))

#-----Excecute The Program-----
if __name__ == "__main__":
    checkDatabase()
    window.mainloop()
        