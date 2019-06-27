#!/bin/bash

NUM_RUNS=1
DEPTH=8
REG_DELAY=200

NET_DELAY=1000
NIC_BUF_SIZE=100
LLC_SIZE=100
MEM_DELAY=900
LLC_DELAY=900
MEM_ACCESS_TIME=100
LLC_ACCESS_TIME=10
REG_ACCESS_TIME=0
REDUCE_SERVICE=500
NUM_HOSTS=1000
SEED=1
BRANCH=dist/branch-5.txt

#for nicType in ddio mem
#do
#    time python othello.py --netDelay ${NET_DELAY} \
#                           --nicType ${nicType} \
#                           --nicBufSize ${NIC_BUF_SIZE} \
#                           --llcSize ${LLC_SIZE} \
#                           --memDelay ${MEM_DELAY} \
#                           --llcDelay ${LLC_DELAY} \
#                           --regDelay ${REG_DELAY} \
#                           --memAccessTime ${MEM_ACCESS_TIME} \
#                           --llcAccessTime ${LLC_ACCESS_TIME} \
#                           --regAccessTime ${REG_ACCESS_TIME} \
#                           --reduceService ${REDUCE_SERVICE} \
#                           --hosts ${NUM_HOSTS} \
#                           --depth ${DEPTH} \
#                           --runs ${NUM_RUNS} \
#                           --branch ${BRANCH} \
#                           --seed ${SEED}
#    cp out/* data/6-22-19/cpu_utilization/${nicType}/
#    cp out/cpu_utilization.csv data/6-22-19/cpu_utilization/${nicType}/cpu-util-${nicType}.csv
#done
#
#for delay in 200 400 600
#do
#    time python othello.py --netDelay ${NET_DELAY} \
#                           --nicType reg \
#                           --nicBufSize ${NIC_BUF_SIZE} \
#                           --llcSize ${LLC_SIZE} \
#                           --memDelay ${MEM_DELAY} \
#                           --llcDelay ${LLC_DELAY} \
#                           --regDelay ${delay} \
#                           --memAccessTime ${MEM_ACCESS_TIME} \
#                           --llcAccessTime ${LLC_ACCESS_TIME} \
#                           --regAccessTime ${REG_ACCESS_TIME} \
#                           --reduceService ${REDUCE_SERVICE} \
#                           --hosts ${NUM_HOSTS} \
#                           --depth ${DEPTH} \
#                           --runs ${NUM_RUNS} \
#                           --branch ${BRANCH} \
#                           --seed ${SEED}
#    cp out/* data/6-22-19/cpu_utilization/reg-${delay}/
#    cp out/cpu_utilization.csv data/6-22-19/cpu_utilization/reg-${delay}/cpu-util-reg-${delay}.csv
#done

# offload experiment
time python othello.py --netDelay ${NET_DELAY} \
                       --nicType reg \
                       --nicBufSize ${NIC_BUF_SIZE} \
                       --llcSize ${LLC_SIZE} \
                       --memDelay ${MEM_DELAY} \
                       --llcDelay ${LLC_DELAY} \
                       --regDelay 200 \
                       --memAccessTime ${MEM_ACCESS_TIME} \
                       --llcAccessTime ${LLC_ACCESS_TIME} \
                       --regAccessTime ${REG_ACCESS_TIME} \
                       --reduceService 0 \
                       --hosts ${NUM_HOSTS} \
                       --depth ${DEPTH} \
                       --runs ${NUM_RUNS} \
                       --branch ${BRANCH} \
                       --seed ${SEED}
cp out/* data/6-22-19/cpu_utilization/reg-offload/
cp out/cpu_utilization.csv data/6-22-19/cpu_utilization/reg-offload/cpu-util-reg-offload.csv

