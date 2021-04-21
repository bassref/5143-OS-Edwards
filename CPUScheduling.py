#!/usr/bin/python
import sys
import random
import threading, queue
import rich
import time
from rich import print
from rich.columns import Columns
from rich import box
from rich import panel
from rich.panel import Panel
from datetime import datetime
from time import sleep
from rich.align import Align
#from rich.console import Console, RenderGroup
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.console import Console
from rich.table import Table
from rich.console import render_group
import random
import json
import sys,os

clockTick = 0
processList = []

console = Console()
layout = Layout()

layout.split(
    Layout(name="main"),
    Layout(name="footer")

)

layout["main"].split_row(
    Layout(name="left"), 
    Layout(name="right")
    #direction="horizontal"
)

layout['left'].ratio = 1
layout['right'].ratio = 1

fcfs_queue = queue.PriorityQueue()
sjf_queue = queue.PriorityQueue()
ps_queue = queue.PriorityQueue()
roundrobin_queue = queue.Queue()


'''
Process Class
Takes the information for each job and creates a queue 
for each scheduling algorithm
'''
class Process:
    def __init__(self, arrTime, ID,Prio, N, C_bursts, I_bursts, mode, ready):
        #instance variables
        self.arrTime = int(arrTime)
        self.ID = int(ID)
        self.Prio = int(Prio)
        self.N = int(N)
        self.CPU_bursts = []
        self.IO_bursts = []
        self.mode = int(mode)
        
        #other attributes about a process
        self.ready = ready
        self.waiting = False
        self.done = False
        
        self.waitTime = 0
        self.burstTime = 0
        self.BT = 0

        for cburst in C_bursts:
            self.CPU_bursts.append(int(cburst))

        for iburst in I_bursts:
            self.IO_bursts.append(int(iburst))

    #checking the arrival time for the priority queue
    def __gt__(self,other):
        if(self.mode == 0):
            if (self.arrTime > other.arrTime):
                return True
            elif(self.arrTime == other.arrTime):
                if(self.ID < other.ID):
                    return True       
            return False
        elif(self.mode == 1):
            if (self.CPU_bursts[0] > other.C_bursts[0]):
                return True
            elif(self.CPU_bursts[0] == other.C_bursts[0]):
                if(self.ID < other.ID):
                    return True       
            return False
        elif(self.mode == 2):
            if (self.Prio > other.Prio):
                return True
            elif(self.Prio == other.Prio):
                if(self.ID < other.ID):
                    return True       
            return False
        elif(self.mode == 3):
            if (self.CPU_bursts[0] > other.C_bursts[0]):
                return True
            elif(self.CPU_bursts[0] == other.C_bursts[0]):
                if(self.ID < other.ID):
                    return True       
            return False
        else:
            return False
   

    def __lt__(self,other):
        if(self.mode == 0):
            if (self.arrTime < other.arrTime):
                return True
            elif(self.arrTime == other.arrTime):
                if(self.ID > other.ID):
                    return True
            return False
        elif(self.mode == 1):
            if (self.CPU_bursts[0] < other.CPU_bursts[0]):
                return True
            elif(self.CPU_bursts[0] == other.CPU_bursts[0]):
                if(self.ID > other.ID):
                    return True
            return False
        elif(self.mode == 2):
            if (self.Prio < other.Prio):
                return True
            elif(self.Prio == other.Prio):
                if(self.ID > other.ID):
                    return True
            return False
        elif(self.mode == 3):
            if (self.CPU_bursts[0] < other.CPU_bursts[0]):
                return True
            elif(self.CPU_bursts[0] == other.CPU_bursts[0]):
                if(self.ID > other.ID):
                    return True
            return False
        else:
            return False
       
      

'''
CPU class
Class that determines how an instance of a CPU functions
'''
class CPU:
    def __init__(self,text):
        self.busy = False
        self.timeleft = 0
        self.currentProcess = Process(-1,-1, 1,-1,[-1],[-1],-1,False)
        self.name = text
    
    def assign(self,process):
        self.busy = True
        self.currentProcess = process
        self.timeleft = process.CPU_bursts[0]
        self.currentProcess.CPU_bursts.pop(0)


    def tick(self):
        #if no process to run
        if(self.currentProcess.ID == -1):
            return

        # print(Panel(CPU_bursts, title="CPU1 Processing"))
        self.timeleft-=1
        if(self.timeleft == 0):
            if(len(self.currentProcess.IO_bursts)):
                self.currentProcess.waiting = True
                self.currentProcess.ready = False
            else:
                self.currentProcess.ready = False
                self.currentProcess.waiting = False
                self.currentProcess.done = True
            
            self.busy = False

    def clear(self):
        self.busy = False
        self.timeleft = 0
        self.currentProcess = Process(-1,-1,-1,-1,[-1],[-1],-1,False)

    

'''
IPU Class
Class that determines how an instance of a IO processing unit functions
'''
class IPU:
    def __init__(self,text):
        self.busy = False
        self.timeleft = 0
        self.currentProcess = Process(-1,-1,-1,-1,[-1],[-1],-1,False)
        self.name = text
    
    def assign(self,process):
        self.busy = True
        self.currentProcess = process
        self.timeleft = process.IO_bursts[0]
        self.currentProcess.IO_bursts.pop(0)

    def tick(self):
        #if no process to run
        if(self.currentProcess.ID == -1):
            return

        # print(Panel(CPU_bursts, title="CPU1 Processing"))
        self.timeleft-=1
        if(self.timeleft == 0):
            if(len(self.currentProcess.CPU_bursts)):
                self.currentProcess.waiting = False
                self.currentProcess.ready = True
            else:
                self.currentProcess.ready = False
                self.currentProcess.waiting = False
            
            self.busy = False

    def clear(self):
        self.busy = False
        self.timeleft = 0
        self.currentProcess = Process(-1,-1,-1,-1,[-1],[-1],-1,False)



'''
Scheduler Function
Schedules jobs to the CPU and IO
'''    
def Scheduler(prioQ,cpuNum,ipuNum):
    console = Console()
    ioQ = queue.PriorityQueue()
    terminated = []
    usage = 0
    #create a table for the precesses
    cpuList = []
    ipuList = []
    for x in range (cpuNum):
        cpuList.append(CPU("cpu"+str(x)))

    for n in range (ipuNum):
        ipuList.append(IPU("ipu"+str(n)))

 
    #while there are jobs inthe queue
    while ((not (prioQ.empty())) or (not (ioQ.empty()))):
        #check CPU usage
        for cpu in cpuList:
            if(cpu.busy):
                usage+=1
        
            #check to see if a CPU is not busy
            if((not cpu.busy) and (not (prioQ.empty()))):
                #send to CPU
                item = prioQ.get()
                cpu.assign(item)
                processList.append((str(item.ID),cpu.name,"Processing"))       
        
            #actually run process on CPU
            cpu.tick()
    
            #if the process on the CPU1 requires IO
            if(cpu.currentProcess.waiting):
                ioQ.put(cpu.currentProcess)
                processList.append((str(cpu.currentProcess.ID),"Wait Queue","Waiting"))
                #table.add_row(str(cpu1.currentProcess.ID),"Wait Queue","Waiting",style="yellow" )
                cpu.clear()
                
            #else if the process has terminated
            elif (cpu.currentProcess.done):
                #add to terminated list
                processList.append((str(cpu.currentProcess.ID),cpu.name,"CPU Burst Completed"))
                terminated.append((cpu.currentProcess.ID, cpu.currentProcess.waitTime, cpu.currentProcess.BT, usage))
                cpu.clear()
 
        #anything in the Ready Queue needs to have its waitTime increased
        for process in prioQ.queue:
            process.BT+=1
        
        for ipu in ipuList:
            #check to see if a IPU1 is not busy
            if((not ipu.busy) and (not (ioQ.empty()))):
                #send to IPU
                item = ioQ.get()
                ipu.assign(item)
                processList.append((str(item.ID),ipu.name,"Processing IO"))

            #actually run process on I/O PU
            ipu.tick()

            #anything in the IO Queue needs to have its waitTime increased
            for process in ioQ.queue:
                process.waitTime+=1

            #has IPU1 finished I/O
            if(ipu.currentProcess.ready):
                processList.append((str(ipu.currentProcess.ID),"Ready Queue","Ready for CPU"))
                prioQ.put(ipu.currentProcess)
                ipu.currentProcess.BT+=1
                processList.append((str(ipu.currentProcess.ID),ipu.name,"IO burst completed"))
                ipu.clear()  
        
        P = printProc(processList)
        T = printTerm(terminated)

        with Live(layout, screen=True, redirect_stderr=False) as live:
            layout["left"].update(P)
            layout["right"].update(T)
            sleep(0.1)
            

    #Table is returned so that final calulations can be done
    return terminated
'''
Class to print the processes
'''
class printProc:
    def __init__(self,pList):
        self.pList = pList

    def makeTable(self):
        table = Table(title="Processing")
        table.add_column("ID", justify="center", style="cyan", no_wrap=True)
        table.add_column("Process", justify="center", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center", style="cyan", no_wrap=True)
        
        #listed = list(self.pList)
        if(not len(self.pList) ==0):
            for item in self.pList:
                IDNum = str(item[0])
                where = str(item[1])
                doing = str(item[2])
                table.add_row(IDNum,where,doing,style="green")

        return table

    def __rich__(self) -> Panel:
        return Panel(self.makeTable())

'''
Class to print the tables of terminated processes
'''
class printTerm:
    def __init__(self,pList):
        self.pList = pList

    def makeTable(self):
        table3 = Table(title="Teminated Processes")
        table3.add_column("Process ID", justify="center", style="#ef7215", no_wrap=True)
        table3.add_column("Wait Time",justify="center", style="cyan",no_wrap=True)
        table3.add_column("Burst Time",justify="center", style="red",no_wrap=True)
        table3.add_column("Turnaround Time",justify="center",style="green",no_wrap=True)

        if(not len(self.pList) ==0):
            for item in self.pList:
                IDNum = str(item[0])
                waitT = str(item[1])
                burstT = str(item[2])
                usage = str(item[3])
                tat = str(item[1]+item[2])
                table3.add_row(IDNum,waitT,burstT,tat, style="yellow")
                #(str(tup[0]), str(tup[1]), str(tup[2]),str(tat))
                #table.add_row(IDNum,waitT,burstT,usage, style="yellow")

        return table3

    def __rich__(self) -> Panel:
        return Panel(self.makeTable())


'''
rrCPU class
Class that determines how an instance of a CPU functions
'''
class rrCPU:

    def __init__(self,text):
        self.QUANTUM = 5
        self.busy = False
        self.timeleft = 0
        self.quantum = self.QUANTUM
        self.currentProcess = Process(-1,-1,-1,-1,[-1],[-1],-1,False)
        self.name = text
    
    def assign(self,process):
        self.busy = True
        self.currentProcess = process
        self.timeleft = process.CPU_bursts[0]
        self.currentProcess.CPU_bursts.pop(0)
        self.quantum = self.QUANTUM

    def clear(self):
        self.busy = False
        self.timeleft = 0
        self.quantum = self.QUANTUM
        self.currentProcess = Process(-1,-1,-1,-1,[-1],[-1],-1,False)

    def preempt(self, prioQ):  
        self.currentProcess.CPU_bursts.insert(0,self.timeleft)
        prioQ.put(self.currentProcess)
        self.clear()

    def tick(self):
        #if no process to run
        if(self.currentProcess.ID == -1):
            return

        # print(Panel(CPU_bursts, title="CPU1 Processing"))
        self.timeleft-=1
        if(self.timeleft == 0):
            if(len(self.currentProcess.IO_bursts)):
                self.currentProcess.waiting = True
                self.currentProcess.ready = False
            else:
                self.currentProcess.ready = False
                self.currentProcess.waiting = False
                self.currentProcess.done = True
            
            self.busy = False
        
        self.quantum-=1

        

'''
rrScheduler Function
Schedules jobs to the CPU and IO
'''    
def rrScheduler(prioQ,cpuNum,ipuNum):
    console = Console()
    ioQ = queue.PriorityQueue()
    terminated = []
    usage = 0
    #create a table for the processes
    cpuList = []
    ipuList = []

    for x in range (cpuNum):
        cpuList.append(rrCPU("cpu"+str(x)))

    for n in range (ipuNum):
        ipuList.append(IPU("ipu"+str(n)))
    
    #while there are jobs inthe queue
    while ((not (prioQ.empty())) or (not (ioQ.empty()))):
        #check CPU usage
        for cpu in cpuList:
            if(cpu.busy):
                usage+=1

            #check to see if a CPU is not busy
            if((not cpu.busy) and (not (prioQ.empty()))):
                #send to CPU
                item = prioQ.get()
                cpu.assign(item)
                processList.append((str(item.ID),cpu.name,"Processing"))       

            #actually run process on CPU
            cpu.tick()
        
        
        
            #if the process on the CPU1 requires IO
            if(cpu.currentProcess.waiting):
                ioQ.put(cpu.currentProcess)
                processList.append((str(cpu.currentProcess.ID),"Wait Queue","Waiting"))
                #table.add_row(str(cpu1.currentProcess.ID),"Wait Queue","Waiting",style="yellow" )
                cpu.clear()

            #else if the process has terminated
            elif (cpu.currentProcess.done):
                #add to terminated list
                processList.append((str(cpu.currentProcess.ID),cpu.name,"CPU Burst Completed"))
                terminated.append((cpu.currentProcess.ID, cpu.currentProcess.waitTime, cpu.currentProcess.BT, usage))
                cpu.clear()
        
        

            #Determine if anything needs to be preempted
            if(cpu.quantum == 0):
                cpu.preempt(prioQ)

        #anything in the Ready Queue needs to have its waitTime increased
        for process in prioQ.queue:
            process.BT+=1 

        for ipu in ipuList:
            #check to see if IPU1 is not busy
            if((not ipu.busy) and (not (ioQ.empty()))):
                #send to IPU
                item = ioQ.get()
                ipu.assign(item)
                processList.append((str(item.ID),ipu.name,"Processing IO"))

            #actually run process on I/O PU
            ipu.tick()

            #anything in the IO Queue needs to have its waitTime increased
            for process in ioQ.queue:
                process.waitTime+=1
                
            #has IPU1 finished I/O
            if(ipu.currentProcess.ready):
                processList.append((str(ipu.currentProcess.ID),"Ready Queue","Ready for CPU"))
                prioQ.put(ipu.currentProcess)
                ipu.currentProcess.BT+=1
                processList.append((str(ipu.currentProcess.ID),ipu.name,"IO burst completed"))
                ipu.clear() 

        P = printProc(processList)
        T = printTerm(terminated)

        with Live(layout, screen=True, redirect_stderr=False) as live:
            layout["left"].update(P)
            layout["right"].update(T)
            sleep(0.1)
    
    return terminated



def printStuff(termTable):
    termin = termTable
    console = Console()
    
    longestWT = termin[0][1]
    shortestWT = termin[0][1]
    sumWT = 0.0
    tat = 0.0
    sumTAT = 0.0
    avgWaitTime = 0.0
    avgTAT = 0.0
    sumUse = 0
    avgUse = 0
    tatPercent = 0
    for tup in termin:
        tat = tup[1]+tup[2]
        sumWT = sumWT + int(tup[1])
        sumTAT = sumTAT+tat
        newWT = tup[1]
        sumUse +=tup[3]
        if(newWT>longestWT):
            longestWT = newWT
        elif(newWT<longestWT):
            shortestWT = newWT
        
    
    avgTAT = sumTAT/ len(termin)
    avgWaitTime = sumWT/ len(termin)
    avgUse = sumUse / len(termin)
    tatPercent = ((avgTAT/len(termin))/2)

        
    # console.print("Shortest wait time = ", str(shortestWT))
    # console.print("Longest wait time = ", str(longestWT))
    # console.print("Average wait time = ", str(avgWaitTime))
    # console.print("Average turnaround time = ", str(avgTAT))
    # console.print("CPU use % = ", str(tatPercent))  

    table2 = Table(title="Summary")
    table2.add_column("Shortest wait time", justify="center", style="#ef7215", no_wrap=True)
    table2.add_column("Longest wait time",justify="center", style="cyan",no_wrap=True)
    table2.add_column("Average wait time",justify="center", style="red",no_wrap=True)
    table2.add_column("Average turnaround time",justify="center",style="green",no_wrap=True)
    table2.add_column("CPU use % =",justify="center",style="green",no_wrap=True)
    table2.add_row(str(shortestWT),str(longestWT),str(avgWaitTime),str(avgTAT), str(tatPercent))

    with Live(layout, screen=True, redirect_stderr=False) as live:
        layout["footer"].update(table2)
        sleep(500)
     


'''
MAIN
'''
if __name__ =="__main__":
    cpuNum = sys.argv[1]
    ipuNum = sys.argv[2]

    # each algorithm has it's own queue
    
    termin = []

    with open('datafile3.dat') as reader:
        lines = reader.read().splitlines()
    
    #iterate through the list of data and assign arrival time and ID then add the remainder to a list
    for item in lines:
        item = item.split(" ")

        arrTime = item[0]
        ID = item[1]
        Prio = item[2]
        N = item[3]
        CPU_bursts = item[4::2]
        IO_bursts = item[5::2]
        #creating the objects
        fcfsinfo = Process(arrTime, ID,Prio, N, CPU_bursts, IO_bursts,0, True)
        sjfinfo = Process(arrTime, ID,Prio, N, CPU_bursts, IO_bursts,1, True)
        psinfo = Process(arrTime, ID,Prio, N, CPU_bursts, IO_bursts,2, True)
        roundrobininfo = Process(arrTime, ID,Prio, N, CPU_bursts, IO_bursts,3, True)
        #adding objects to the queue
        fcfs_queue.put(fcfsinfo)
        sjf_queue.put(sjfinfo)
        ps_queue.put(psinfo)
        roundrobin_queue.put(roundrobininfo)

    #pass a job to the scheduler
    #termin = Scheduler(fcfs_queue,int(cpuNum),int(ipuNum))
    #termin = Scheduler(sjf_queue,int(cpuNum),int(ipuNum))
    #termin = Scheduler(ps_queue,int(cpuNum),int(ipuNum))
    termin = rrScheduler(roundrobin_queue,int(cpuNum),int(ipuNum))
          
    printStuff(termin)
    
   
    