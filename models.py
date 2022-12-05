from tortoise import fields
from tortoise.models import Model

class GraphStats(Model):
    ID = fields.UUIDField(pk=True)

class Graphs(Model):
    ID = fields.IntField(pk=True)
    Title = fields.TextField()
    relation: fields.ReverseRelation["Transit"]

class Transit(Model):
    ID = fields.UUIDField(pk=True)
    graph: fields.ForeignKeyRelation[Graphs] = fields.ForeignKeyField("models.Graphs", related_name="relation")
    DateTime = fields.BigIntField()
    Outbound = fields.FloatField()
    InBound = fields.FloatField()


