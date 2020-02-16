# This script is used from python when the trident and sparql nodes will finish
# it will reserve new nodes

# Elastic search
ES_PORT=9200
ES_BIN=/var/scratch/wdps1934/wdps/elasticsearch-2.4.1/bin/elasticsearch

# Trident
KB_PORT=9090
KB_BIN=/home/jurbani/trident/build/trident
KB_PATH=/home/jurbani/data/motherkb-trident


# starting Elastic search
prun -o .es_log -v -np 1 ESPORT=$ES_PORT $ES_BIN </dev/null 2> .es_node &
#echo "waiting for elasticsearch to set up..."
until [ -n "$ES_NODE" ]; do ES_NODE=$(cat .es_node | grep '^:' | grep -oP '(node...)'); done
ES_PID=$!
until [ -n "$(cat .es_log* | grep YELLOW)" ]; do sleep 1; done
#echo "elasticsearch should be running now on node $ES_NODE:$ES_PORT (connected to process $ES_PID)"

sleep 5
#####################################

# starting Trident
#echo "Lauching an instance of the Trident server on a random node in the cluster ..."
prun -o .kb_log -v -np 1 $KB_BIN server -i $KB_PATH --port $KB_PORT </dev/null 2> .kb_node &
#echo "Waiting 5 seconds for trident to set up (use 'preserve -llist' to see if the node has been allocated)"
until [ -n "$KB_NODE" ]; do KB_NODE=$(cat .kb_node | grep '^:' | grep -oP '(node...)'); done

sleep 5
KB_PID=$!
#echo "Trident should be running now on node $KB_NODE:$KB_PORT (connected to process $KB_PID)"
#####################################

# return the results the results so python script will be able to get the NODEs and PORTs
ES_DOMAIN=$ES_NODE:$ES_PORT
KB_DOMAIN=$KB_NODE:$KB_PORT
echo ES_DOMAIN KB_DOMAIN