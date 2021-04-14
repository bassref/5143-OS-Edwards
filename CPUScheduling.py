import sys
import random
import threading, queue
import rich
import time
# from rich import layout
from rich import print
# from rich import console
# from rich import columns
from rich.columns import Columns
# from rich.console import Console
from rich.table import Table
from rich import box
from rich import panel
from rich.panel import Panel
from datetime import datetime
from time import sleep
from rich.align import Align
from rich.console import Console, RenderGroup
from rich.layout import Layout
from rich.live import Live
from rich.text import Text

clockTick = 0



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
    def __init__(self):
        self.busy = False
        self.timeleft = 0
        self.currentProcess = Process(-1,-1, 1,-1,[-1],[-1],-1,False)
    
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
    def __init__(self):
        self.busy = False
        self.timeleft = 0
        self.currentProcess = Process(-1,-1,-1,-1,[-1],[-1],-1,False)
    
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
def Scheduler(prioQ):
    console = Console()
    #create a table for the precesses
    table = Table(title="Processing", expand=True)
    table.add_column("ID")
    table.add_column("Process")
    table.add_column("Status")

    cpu1 = CPU()
    cpu2 = CPU()
    ipu1 = IPU()
    ipu2 = IPU()
    ioQ = queue.PriorityQueue()
    terminated = []
    usage = 0
    
    #while there are jobs inthe queue
    while (prioQ.qsize() or ioQ.qsize()):
        #check CPU usage
        if(cpu1.busy):
            usage+=1
        if(cpu2.busy):
            usage+=1
        #check to see if a CPU is not busy
        if((not cpu1.busy) and prioQ.qsize()):
            #send to CPU
            item = prioQ.get()
            cpu1.assign(item)
            table.add_row(str(item.ID),"CPU1","Processing",style="green")
            

        if((not cpu2.busy) and prioQ.qsize()):
            item = prioQ.get()
            cpu2.assign(item)
            table.add_row(str(item.ID),"CPU2","Processing",style="green")
            
        
        #actually run process on CPU
        cpu1.tick()
        cpu2.tick()       

        #anything in the Ready Queue needs to have its waitTime increased
        for process in prioQ.queue:
            process.BT+=1
        
        #if the process on the CPU1 requires IO
        if(cpu1.currentProcess.waiting):
            ioQ.put(cpu1.currentProcess)
            table.add_row(str(cpu1.currentProcess.ID),"Wait Queue","Waiting",style="yellow" )
            cpu1.clear()
            
        #else if the process has terminated
        elif (cpu1.currentProcess.done):
            #add to terminated list
            terminated.append((cpu1.currentProcess.ID, cpu1.currentProcess.waitTime, cpu1.currentProcess.BT, usage))
            cpu1.clear()
        
        #if the process on the CPU2 requires IO
        if(cpu2.currentProcess.waiting):
            ioQ.put(cpu2.currentProcess)
            table.add_row(str(cpu2.currentProcess.ID),"Wait Queue","Waiting",style="yellow" )
            cpu2.clear()
        #else if the process has terminated
        elif (cpu2.currentProcess.done):
            #add to terminated list
            terminated.append((cpu2.currentProcess.ID, cpu2.currentProcess.waitTime, cpu2.currentProcess.BT, usage))
            cpu2.clear()

        #check to see if a IPU1 is not busy
        if((not ipu1.busy) and ioQ.qsize()):
            #send to IPU
            item = ioQ.get()
            ipu1.assign(item)
            table.add_row(str(item.ID),"IPU1","Processing IO", style="#ff6f68" )
        
        #check to see if a IPU2 is not busy
        if((not ipu2.busy) and ioQ.qsize()):
            #send to IPU
            item = ioQ.get()
            ipu2.assign(item)
            table.add_row(str(item.ID),"IPU2","Processing IO", style="#ff6f68" )
        
        #actually run process on I/O PU
        ipu1.tick()
        ipu2.tick()
        
        #anything in the IO Queue needs to have its waitTime increased
        for process in ioQ.queue:
            process.waitTime+=1

        #has IPU1 finished I/O
        if(ipu1.currentProcess.ready):
            table.add_row(str(ipu1.currentProcess.ID),"Ready Queue","Ready for CPU", style="red" )
            prioQ.put(ipu1.currentProcess)
            ipu1.currentProcess.BT+=1
            table.add_row(str(ipu1.currentProcess.ID),"IPU1","IO burst completed", style="blue" )
            ipu1.clear()
        #has IPU1 finished I/O
        if(ipu2.currentProcess.ready):
            table.add_row(str(ipu2.currentProcess.ID),"Ready Queue","Ready for CPU", style="red" )
            prioQ.put(ipu2.currentProcess)
            ipu2.currentProcess.BT+=1
            table.add_row(str(ipu2.currentProcess.ID),"IPU2","IO burst completed", style="blue" )
            ipu2.clear()

    time.sleep(1)
    console.print(table)
    return terminated


'''
rrCPU class
Class that determines how an instance of a CPU functions
'''
class rrCPU:

    def __init__(self):
        self.QUANTUM = 5
        self.busy = False
        self.timeleft = 0
        self.quantum = self.QUANTUM
        self.currentProcess = Process(-1,-1,-1,-1,[-1],[-1],-1,False)
    
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
def rrScheduler(prioQ):
    console = Console()
    table = Table(title="Processing", expand=True)
    table.add_column("ID")
    table.add_column("Process")
    table.add_column("Status")
    cpu1 = rrCPU()
    cpu2 = rrCPU()
    ipu1 = IPU()
    ipu2 = IPU()
    ioQ = queue.Queue()
    terminated = []
    usage = 0
    
    #while there are jobs inthe queue
    while (prioQ.qsize() or ioQ.qsize()):
        #checking for usage
        #check CPU usage
        if(cpu1.busy):
            usage+=1
        if(cpu2.busy):
            usage+=1
        #check to see if CPU1 is not busy
        if((not cpu1.busy) and prioQ.qsize()):
            #send to CPU
            item = prioQ.get()
            cpu1.assign(item)
            table.add_row(str(item.ID),"CPU1","Processing", style="green" )
            
        #check to see if CPU2 is not busy
        if((not cpu2.busy) and prioQ.qsize()):
            item = prioQ.get()
            cpu2.assign(item)
            table.add_row(str(item.ID),"CPU2","Processing", style="green" )
            
        
        #actually run process on CPU
        cpu1.tick()
        cpu2.tick()   

        #anything in the Ready Queue needs to have its waitTime increased
        for process in prioQ.queue:
            process.BT+=1
        
        #if the process on the CPU1 requires IO
        if(cpu1.currentProcess.waiting):
            ioQ.put(cpu1.currentProcess)
            table.add_row(str(cpu1.currentProcess.ID),"Wait Queue","Waiting" , style="yellow")
            cpu1.clear()
        #else if process has terminated
        elif (cpu1.currentProcess.done):
            #add to terminated list
            terminated.append((cpu1.currentProcess.ID, cpu1.currentProcess.waitTime, cpu1.currentProcess.BT, usage))
            cpu1.clear()
        
        #if the process on the CPU1 requires IO
        if(cpu2.currentProcess.waiting):
            ioQ.put(cpu2.currentProcess)
            table.add_row(str(cpu2.currentProcess.ID),"Wait Queue","Waiting",style="yellow" )
            cpu2.clear()
        #else if process has terminated
        elif (cpu2.currentProcess.done):
            #add to terminated list            
            terminated.append((cpu2.currentProcess.ID, cpu2.currentProcess.waitTime, cpu2.currentProcess.BT,usage))
            cpu2.clear()

        #Determine if anything needs to be preempted
        if(cpu1.quantum == 0):
            cpu1.preempt(prioQ)
        if(cpu2.quantum == 0):
            cpu2.preempt(prioQ)

        #check to see if IPU1 is not busy
        if((not ipu1.busy) and ioQ.qsize()):
            #send to IPU
            item = ioQ.get()
            ipu1.assign(item)
            table.add_row(str(item.ID),"IPU1","Processing IO", style="#ff6f68" )      
        
        #check to see if IPU2 is not busy
        if((not ipu2.busy) and ioQ.qsize()):
            #send to IPU
            item = ioQ.get()
            ipu2.assign(item)
            table.add_row(str(item.ID),"IPU1","Processing IO", style="#ff6f68" )
        
        #actually run process on I/O PU
        ipu1.tick()
        ipu2.tick()

        #anything in the IO Queue needs to have its waitTime increased
        for process in ioQ.queue:
            process.waitTime+=1
                
        #has IPU1 finished I/O
        if(ipu1.currentProcess.ready):
            table.add_row(str(ipu1.currentProcess.ID),"Ready Queue","Ready for CPU", style="red" )
            prioQ.put(ipu1.currentProcess)
            ipu1.currentProcess.BT+=1
            table.add_row(str(ipu1.currentProcess.ID),"IPU1","IO burst completed", style="blue" )
            ipu1.clear()
        #has IPU2 finished I/O        
        if(ipu2.currentProcess.ready):
            table.add_row(str(ipu2.currentProcess.ID),"Ready Queue","Ready for CPU", style="red" )
            prioQ.put(ipu2.currentProcess)
            ipu2.currentProcess.BT+=1
            table.add_row(str(ipu2.currentProcess.ID),"IPU2","IO burst completed",style="blue" )
            ipu2.clear()
        
    console.print(table)
    return terminated


'''
MAIN
'''
if __name__ =="__main__":

    # each algorithm has it's own queue
    fcfs_queue = queue.PriorityQueue()
    sjf_queue = queue.PriorityQueue()
    ps_queue = queue.PriorityQueue()
    roundrobin_queue = queue.Queue()
    termin = []

    with open('datafile2.dat') as reader:
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
    #termin = Scheduler(fcfs_queue)
    #termin = Scheduler(sjf_queue)
    termin = Scheduler(ps_queue)
    #termin = rrScheduler(roundrobin_queue)
   
    #add terminated list to a table
    console = Console()
    table3 = Table(title="Teminated Processes")
    table3.add_column("Prcess ID", style="#ef7215")
    table3.add_column("Wait Time",style="#ef7215")
    table3.add_column("Burst Time",style="#ef7215")
    table3.add_column("Turnaround Time",style="#ef7215")
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
        table3.add_row(str(tup[0]), str(tup[1]), str(tup[2]),str(tat))
        sumWT = sumWT + int(tup[1])
        sumTAT = sumTAT+tat
        newWT = tup[1]
        sumUse +=tup[3]
        if(newWT>longestWT):
            longestWT = newWT
        elif(newWT<longestWT):
            shortestWT = newWT
        time.sleep(1)  
    
    avgTAT = sumTAT/ len(termin)
    avgWaitTime = sumWT/ len(termin)
    avgUse = sumUse / len(termin)
    tatPercent = ((avgTAT/len(termin))/2)
    console.print(table3)
    console.print("Shortest wait time = ", shortestWT)
    console.print("Longest wait time = ", longestWT)
    console.print("Average wait time = ", avgWaitTime)
    console.print("Average turnaround time = ", avgTAT)
    console.print("CPU use % = ", tatPercent)