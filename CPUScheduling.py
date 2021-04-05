import random
from rich import print
from rich.console import Console
from rich.table import Table
from rich import box


# Driver code
if __name__ =="__main__":
	
    schedule = Scheduling()
    # process id's
    processes = ['read', 'write','I/O'] 
    n = len(processes)

    # Burst time of all processes
    burst_time = [random.randint(1,n), random.randint(1,n), random.randint(1,n)]#[10, 5, 8]

    schedule.FCFS(processes, n, burst_time)

# This code is contributed
# by ChitraNayal

# Class with scheduling algorithms
class Scheduling:

    def FCFS(self, processes, n, burst_time):
        # Python3 program for implementation
        # of FCFS scheduling

        # Function to find the waiting
        # time for all processes
        def findWaitingTime(processes, n,
                            bt, wt):

            # waiting time for
            # first process is 0
            wt[0] = 0

            # calculating waiting time
            for i in range(1, n ):
                wt[i] = bt[i - 1] + wt[i - 1]

        # Function to calculate turn
        # around time
        def findTurnAroundTime(processes, n,
                            bt, wt, tat):

            # calculating turnaround
            # time by adding bt[i] + wt[i]
            for i in range(n):
                tat[i] = bt[i] + wt[i]

        # Function to calculate
        # average time
        def findavgTime( processes, n, bt):

            wt = [0] * n
            tat = [0] * n
            total_wt = 0
            total_tat = 0

            # Function to find waiting
            # time of all processes
            findWaitingTime(processes, n, bt, wt)

            # Function to find turn around
            # time for all processes
            findTurnAroundTime(processes, n,
                            bt, wt, tat)

            # Display processes along
            # with all details
            table = Table(title="CPU Processes")
            table.add_column("Process ", justify="center", style="yellow", no_wrap=True)
            table.add_column("Burst time", justify="center",style="magenta")
            table.add_column(" Waiting time ", justify="center", style="cyan")
            table.add_column(" Turn around time", justify="center", style="green")

            # Calculate total waiting time
            # and total turn around time
            for i in range(n):
            
                total_wt = total_wt + wt[i]
                total_tat = total_tat + tat[i]
                table.add_row(processes[i], str(bt[i]), str(wt[i]), str(tat[i]) )
                
            #str(i + 1)
            print( "Average waiting time = "+
                        str(total_wt / n))
            print("Average turn around time = "+
                            str(total_tat / n))
            console = Console()
            console.print(table)
    