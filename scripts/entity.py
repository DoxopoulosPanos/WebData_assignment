"""
This module implements the class Entity
"""


class Entity:

    def __init__(self, name):
        self.name = name
        self.freebase_id = None
        self.freebase_label = None

    def set_freebase_values(self, freebase_id, freebase_label):
        self.freebase_id = freebase_id
        self.freebase_label = freebase_label

    def __str__(self):
        return "Entity____  NAME: {} , ID: {} , LABEL: {}".format(self.name, self.freebase_id, self.freebase_id)

