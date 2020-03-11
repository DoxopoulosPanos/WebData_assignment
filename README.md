# Assignment: Web Data and Processing Systems
## Entity Linking
Assignment for the course Web Data and Processing Systems (Vrije University of Amsterdam) - NLP pipeline and Entity Linking

### 1. How to execute

The project is on DAS-4 (VU cluster) at the folder /var/scratch/wdps1934/WebData_assignment/

In the environment of the user wdps1934 everything is installed and ready to run. For running in a different user please install the dependencies (there is a file dependencies.sh inside the folder scripts which include all the necessary libraries.)
To execute it please run "bash dependencies.sh"

Executing the following code will reserve 2 nodes for freebase and trident for 1 hour and it will run the python script on a third node.
The results will be available at the file output.tsv

```
cd /var/scratch/wdps1934/WebData_assignment/scripts
bash run.sh ../../wdps/data/sample.warc.gz > output.tsv
```
Instead of the sample input "../../wdps/data/sample.warc.gz" you can use another file

For better F1 score please increase the reservation time in the 5th line of the run.sh
```
# Time to reserve the node
TIME=21600
```

The program is written in python 2.


### 2. Folder structure

This section describes the structure of the folders and files.

The main folder WebData_assignment contains:
- the README file
- the folder scripts, which contains all the code:
  - run.sh: the script that reserves nodes on the cluster and runs elastic search and Trident and start the python script for entity linking
  - dependencies.sh: a shell script with all the installations that are needed in order to execute the run.sh
  - linker.py: the python script, which is called from run.sh and performs entity linking. It contains all the function for the linking procedure. It uses all the other python scripts.
  - preprocessing.py: the python script that is called from the linker.py in order to process the warc file. In each document in the warc file it performs NLP pipeline (tokinazation, lemmatization, stopword removal, POS tagging, and NER tagging - only for the second method). It detects the entities and returns them in the linker.py
  - entity.py: A module with the class Entity. It is used for the candidates retrieved from freebase.
  - sparql.py: Contains a function that makes request to the Knowledge Base using sparql.
  - elastic_search.py: Contains functions that retrieve the candidates from freebase.


### 3. Design
In this section an overview of the algorithm will be given.

#### 3.1 NLP Preprocessing
The purpose of preprocessing is to clear the information of the records and then find the mentions existing in the text. Steps:

1. Preprocess HTML pages
2. Get WARC_ID from headers
3. Split the body into records
4. Remove unnecessary data (removing code blocks and comments, keep acronyms)
5. NLP pipeline. Tokenization, lemmatization, stopword removal and pos tagging are taking place in this step. After tokenization we also remove all the alphanumerics, hex etc. POS tagging is achieved with the use of the module pos_tag of the nltk library. Additionally, after POS tagging we group the consecutive words classified with the same POS label.
Find Entity Mentions in each record. We consider as entities all the tokens than were classified as NNP by the nltk POS tagger. The reason of this selection is that the mentions are names of persons, companies etc which are defined as NNP in Penn treebank set.

Another step of the NLP preprocessing is the NER tagging. The main algorithm does not include this step. A second algorithm (METHOD=2, this can be defined in the beginning of the file preprocessing.py) uses the module ne_chunk from nltk library and finds and classifies all tokens according to their NER type. If the NER label of a word is PERSON, ORGANIZATION, or GPE then they are considered as mentions. This algorithm also groups consecutive words with the same NER label.

The results of the second method are disappointing mainly because we use the same algorithm to define entities in the sparql abstract (see next section). The entities returned are just a few and the similarity measurement between the mention and the candidate is not accurate. In order for this method to return a few results, it is needed to decrease the similarity score threshold for defining a mention as unlinkable (e.g. 0.05 or 0.1). This can be defined in the linker.py in the 13th line:
```
THRESHOLD_FOR_UNLINKABLE_MENTION = 0.2
```
The initial purpose of this algorithm was to implement matching between the NER type of the mention and the NER type of the candidate.


#### 3.2 Entity Linking

The purpose in entity linking is to generate entities that could potentially match to the entity mentions of the documents. In order to be able to achieve this, we query the freebase by using elastic search for each of the mentions detected in the previous stage. Elastic search is running on a node in DAS-4 cluster. The candidates retrieved from elastic search should be evaluated and only one of them should be selected as the best match. This is achieved in the disambiguation step. Trident, which is a combination of four Knowledge Bases, is running on another node in DAS-4 and allows sparql queries to get information about each candidate. For this assignment, an abstract of each candidate is retrieved from trident.

<b>Candidate Generation</b>

For each mention query the Freebase (Elastic Search) to retrieve 100 results matching the mention. From those results we use the popularity score (context independent feature) as returned from Freebase and we keep the best 10.

<b>Candidate Ranking</b>

Query Trident using SPARQL and get the abstract for each result. Keep only the English abstracts.
Find and classify the mentions of each abstract. (We consider as entities all the tokens than were classified as NNP by the nltk POS tagger)
Find the BEST matching (Word Sense Disambiguation). We look for similarities between mentions in each record and mentions in SPARQL abstract. This step implements a context-independent feature called Bag Of Words. As we use the words of the whole document trying to figure out if the candidate is an appropriate solution for the mention. In more detail, we detect entities in the trident’s abstract. For each entity in the abstract we use Hamming distance to find the distance with each mention of the document. If the distance is above the threshold (after a few experiments, 0.8 seems a good threshold) we increase a counter. We normalize the counter by dividing it with the number of entities found in the abstract. Then we keep the best candidate according to the aforementioned score. In order to increase the precision, if the best candidate has score less than 0.02 then we consider this mention as false positive and we do not print it. In other words we define it as Unlinkable Mention Entity.

<b>Unlinkable Mention Prediction</b>

The entity mentions that couldn’t be linked are not taken into consideration. Moreover, in case the best candidate has similarity score below the threshold 0.2 it is considered as inaccurate linking and therefore defined as unlinkable.


### 4. Results

After one hour of running the algorithm usually detects 5-7 correct entities. The algorithm is considered slow, since it was able to search in only 6 documents.
```
Gold entities: 560
Linked entities: 61
Correct mappings: 7
Precision: 0.11475409836065574
Recall: 0.0125
F1: 0.022544283413848634
```
Increasing the running time to 6 hours the algorithm managed to process 12 records/documents and achieved a better F1 score:
```
Gold entities: 560
Linked entities: 169
Correct mappings: 12
Precision: 0.07100591715976332
Recall: 0.02142857142857143
F1: 0.03292181069958847
```
We observe that the recall has improved since we found more correct mappings, but the precision got worse as there are many linked entities that are not included in the golden entities. Overall, the F1 score has improved. Possibly, a bigger execution in duration could have an even better result.

### 5. Future work
The program is not focusing on scalability issues. In order to improve scalability, spark can be used, as it is the most common framework for linking. Moreover, identifying relations in the text could improve the precision of the linking. Last but not least, another metric that could be improved is the Bag Of Words (BOW). The algorithm keeps only the mentions found in the record as the BOW of each mention. One idea that could potentially improve the results is to add the most frequent Nouns (NN, NNS) found in each document during the POS tagging.
