"""
This module implements the class Entity
"""


class Entity:

    def __init__(self, name):
        self.name = name
        self.freebase_id = None
        self.freebase_label = None
        self.kb_abstract = None
        self.kb_nouns = None
        self.similarity_score = None

    def __str__(self):
        return "Entity____  NAME: {} , ID: {} , LABEL: {}".format(self.name, self.freebase_id, self.freebase_label)

