from tortoise import fields
from tortoise.models import Model



class Graphs(Model):
    ID = fields.IntField(pk=True, unique=True)
    rawTitle = fields.TextField(null=False)
    POI_state = fields.TextField(null=True, description="State that the POI is managed by")
    POI_server = fields.TextField(null=True)
    POI_code = fields.CharField(4, unique=True, null=True)
    state = fields.TextField(null=True, description="State the POI is based in")
    NBN_CVC = fields.CharField(15, null=True, unique=True)
    CSA = fields.CharField(15, null=True, unique=True)
    VLink_Circuit_ID = fields.CharField(11,null=True, unique=True)
    max_bandwidth = fields.IntField(null=True)
    location = fields.TextField(null=True)
    relation: fields.ReverseRelation["Transit"]


class Transit(Model):
    ID = fields.UUIDField(pk=True, unique=True)
    graph: fields.ForeignKeyRelation[Graphs] = fields.ForeignKeyField("models.Graphs", related_name="relation")
    DateTime = fields.DatetimeField()
    Inbound = fields.FloatField(description="bps")
    Outbound = fields.FloatField(description="bps")
    Bandwidth = fields.FloatField(description="bps")
    Bandwidth_RoC = fields.FloatField(description="bps^2")


