"""
This module implements the classes Mention and Candidate
"""


class Entity(object):

    def __init__(self, name):
        self.name = name
        self.ner_label = None


class Mention(Entity):

    def __init__(self, name, warc_id):
        super(Mention, self).__init__(name)
        self.warc_id = warc_id
        self.record_mentions = None
        self.best_candidate = None

    def __str__(self):
        return "Entity____  NAME: {}  WARC_ID: {}  LABEL: {}".format(self.name, self.warc_id, self.ner_label)


class Candidate(Entity):

    def __init__(self, name):
        super(Candidate, self).__init__(name)
        self.freebase_id = None
        self.freebase_label = None
        self.kb_abstract = None
        self.kb_nouns = None
        self.similarity_score = None

        def __str__(self):
            return "Entity____  NAME: {} , ID: {} , LABEL: {}".format(self.name, self.freebase_id, self.freebase_label)

