
import pprint
from collections import UserDict
from marshmallow import post_load, Schema, fields, utils

class Deserializable(UserDict):
    def __repr__(self):
        return pprint.pformat(self.__dict__, indent=2)


class DeserializableSchema(Schema):
    object_class = Deserializable

    @post_load
    def make_instance(self, data):
        return self.object_class(**data)
