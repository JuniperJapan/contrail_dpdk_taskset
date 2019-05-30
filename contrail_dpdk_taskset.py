#!/bin/python

from argparse import ArgumentParser
import commands
import re
import sys

# Get contrail-vrouter-dpdk threads.

# Following is test data.
#  28732 contrail-vroute
#  28759 vfio-sync
#  28853 eal-intr-thread
#  28854 lcore-slave-1
#  28855 lcore-slave-2
#  28856 lcore-slave-8
#  28857 lcore-slave-9
#  28858 lcore-slave-10
#  28859 lcore-slave-11
#  28860 lcore-slave-12
#  28861 lcore-slave-13
#  29222 contrail-vroute
#  29542 contrail-vroute
#  29543 contrail-vroute
#  29544 contrail-vroute
#  29545 contrail-vroute
#  29546 contrail-vroute
#  29547 contrail-vroute
#  29548 contrail-vroute
#  29549 contrail-vroute

def check_process():
    command='ps -wLC contrail-vrouter-dpdk -o lwp,comm|sed -e 1,1d|sort -n -k 1,1'
    res = commands.getstatusoutput(command)[1]
    if res == '':
        sys.exit()
    return(0)

def auto_taskset_val():
    isolatecpu_list = []
    pattern = r"[0-9]*-[0-9]*"
    # Get isolate config from cpu-partitioning-variables.conf.
    temp_isolatecpu_list = list((commands.getoutput("cat /etc/tuned/cpu-partitioning-variables.conf |grep -v -e ^$ -e ^#|awk -F= '{print $2}'")).split(','))
    for n in temp_isolatecpu_list:
        expansion_cpunum = re.match(pattern, n)
        if expansion_cpunum:
            temp_expansion_cpunum = list(n.split('-'))
            isolatecpu_list = isolatecpu_list + list(range(int(temp_expansion_cpunum[0]),int(temp_expansion_cpunum[1])+1))
        else:
            isolatecpu_list.append(int(n))
    isolatecpu_list = [str(n) for n in isolatecpu_list]
    print('isolatecpu:')
    print(isolatecpu_list)

    temp_hostcpu_list = list(commands.getoutput("lscpu |grep On-line|awk -F: '{print $2}'|sed -e 's/ //g'").split('-'))
    hostcpu_list = list(range(int(temp_hostcpu_list[0]),int(temp_hostcpu_list[1])+1))
    hostcpu_list = [str(n) for n in hostcpu_list]
    for isolate_cpu in isolatecpu_list:
        hostcpu_list.remove(isolate_cpu)
    print('hostcpu:')
    print(hostcpu_list)

    return ','.join(hostcpu_list)

def do_taskset(tasksetval):
    pattern = r"lcore-slave-[1-9][0-9]"
    command='ps -wLC contrail-vrouter-dpdk -o lwp,comm|sed -e 1,1d|sort -n -k 1,1'

    res = commands.getstatusoutput(command)
    if res[0] == 0:
        cmd_output = commands.getoutput(command)
        #  Create dictionary like as a [PID]:[PROCESS NAME].
        process_d = dict(zip(cmd_output.split()[0::2], cmd_output.split()[1::2]))
        for pid in list(process_d.keys()):
            process = process_d[pid]
            forwarding_process = re.match(pattern, process)
            if forwarding_process:
                process_d.pop(pid)
            else:
                print('taskset target -> ' + pid + ':' + process_d[pid])
                cmd_output = commands.getoutput('taskset -pc' + ' ' + tasksetval + ' ' + pid)
                print(cmd_output)
                print('')
    else:
        print('Command fails')

if __name__ == '__main__':
    check_process()
    tasksetval = (auto_taskset_val())
    do_taskset(tasksetval)
    print('done')
