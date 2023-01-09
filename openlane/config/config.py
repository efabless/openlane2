import json
from decimal import Decimal

from marshmallow.fields import String, List

from .base import Deserializable, DeserializableSchema
from .resolve import resolve


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o.as_integer_ratio()[1] == 1:
                return int(o)
            else:
                return float(o)
        return super(DecimalEncoder, self).default(o)


class DecimalDecoder(json.JSONDecoder):
    def default(self, o):
        if isinstance(o, float) or isinstance(o, int):
            return Decimal(o)
        return super(DecimalDecoder, self).default(o)


class Config(Deserializable):
    @classmethod
    def from_json(Self, json_in: str, **kwargs) -> "Config":
        resolved = resolve(
            json.loads(json_in, cls=DecimalDecoder),
            **kwargs,
        )

        config = Self()  # TODO: Schema Validation
        config.update(resolved)
        return config

    def to_json(self) -> str:
        return json.dumps(self.data, indent=2, cls=DecimalEncoder, sort_keys=True)


class ConfigSchema(DeserializableSchema):
    object_class = Config
    DESIGN_NAME = String()
    VERILOG_FILES = List(String())
    # To be continued
