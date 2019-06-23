#!/bin/bash

NUM_RUNS=2
DEPTH=5

NET_DELAY=1000
NIC_BUF_SIZE=100
LLC_SIZE=100
MEM_DELAY=900
LLC_DELAY=900
REG_DELAY=200
MEM_ACCESS_TIME=100
LLC_ACCESS_TIME=10
REG_ACCESS_TIME=0
REDUCE_SERVICE=500
NUM_HOSTS=2500

for nicType in reg ddio mem
do
    time python othello --netDelay ${NET_DELAY} \
                        --nicType ${nicType} \
                        --nicBufSize ${NIC_BUF_SIZE} \
                        --llcSize ${LLC_SIZE} \
                        --memDelay ${MEM_DELAY} \
                        --llcDelay ${LLC_DELAY} \
                        --regDelay ${REG_DELAY} \
                        --memAccessTime ${MEM_ACCESS_TIME} \
                        --llcAccessTime ${LLC_ACCESS_TIME} \
                        --regAccessTime ${REG_ACCESS_TIME} \
                        --reduceService ${REDUCE_SERVICE} \
                        --hosts ${NUM_HOSTS} \
                        --depth ${DEPTH} \
                        --runs ${NUM_RUNS}
    cp out/completion_times.csv data/6-22-19/completion_times/completion_times-${nicType}.csv
done

# run the simulation with reduce offload enabled
time python othello --netDelay ${NET_DELAY} \
                    --nicType reg \
                    --nicBufSize ${NIC_BUF_SIZE} \
                    --llcSize ${LLC_SIZE} \
                    --memDelay ${MEM_DELAY} \
                    --llcDelay ${LLC_DELAY} \
                    --regDelay ${REG_DELAY} \
                    --memAccessTime ${MEM_ACCESS_TIME} \
                    --llcAccessTime ${LLC_ACCESS_TIME} \
                    --regAccessTime ${REG_ACCESS_TIME} \
                    --reduceService 0 \
                    --hosts ${NUM_HOSTS} \
                    --depth ${DEPTH} \
                    --runs ${NUM_RUNS}
cp out/completion_times.csv data/6-22-19/completion_times/completion_times-reg-offload.csv

