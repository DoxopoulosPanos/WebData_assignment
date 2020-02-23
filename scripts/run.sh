# allow prun command to be executed
module load prun

# Time to reserve the node
TIME=21600

# Elastic search
ES_PORT=9200
ES_BIN=/var/scratch/wdps1934/wdps/elasticsearch-2.4.1/bin/elasticsearch

# Trident
KB_PORT=9090
KB_BIN=/home/jurbani/trident/build/trident
KB_PATH=/home/jurbani/data/motherkb-trident


# starting Elastic search
>.es_log*
prun -t $TIME -o .es_log -v -np 1 ESPORT=$ES_PORT $ES_BIN </dev/null 2> .es_node &
#echo "waiting for elasticsearch to set up..."
until [ -n "$ES_NODE" ]; do ES_NODE=$(cat .es_node | grep '^:' | grep -oP '(node...)'); done
ES_PID=$!
until [ -n "$(cat .es_log* | grep YELLOW)" ]; do sleep 1; done
#echo "elasticsearch should be running now on node $ES_NODE:$ES_PORT (connected to process $ES_PID)"

sleep 5
#####################################

# starting Trident
#echo "Lauching an instance of the Trident server on a random node in the cluster ..."
prun -t $TIME -o .kb_log -v -np 1 $KB_BIN server -i $KB_PATH --port $KB_PORT </dev/null 2> .kb_node &
#echo "Waiting 5 seconds for trident to set up (use 'preserve -llist' to see if the node has been allocated)"
until [ -n "$KB_NODE" ]; do KB_NODE=$(cat .kb_node | grep '^:' | grep -oP '(node...)'); done

sleep 10
KB_PID=$!
#echo "Trident should be running now on node $KB_NODE:$KB_PORT (connected to process $KB_PID)"
#####################################

#python elasticsearch.py $ES_NODE:$ES_PORT "Vrije Universiteit Amsterdam"

#prun -v -np 1 python preprocessing.py "/var/scratch/wdps1934/wdps/data/sample.warc.gz"
if [ $# -eq 0 ]
  then
    echo "NO arguments supplied. Using the file /var/scratch/wdps1934/wdps/data/sample.warc.gz as input"
    prun -t $TIME -v -np 1 python2 linker.py $ES_NODE:$ES_PORT $KB_NODE:$KB_PORT "/var/scratch/wdps1934/wdps/data/sample.warc.gz"
  else
    # argument is given
    prun -t $TIME -v -np 1 python2 linker.py $ES_NODE:$ES_PORT $KB_NODE:$KB_PORT $1
fi

#prun -v -np 1 python elasticsearch.py $ES_NODE:$ES_PORT "Vrije Universiteit Amsterdam"


# kill elastic search server
kill $ES_PID
# kill trident
kill $KB_PID