from tortoise import fields
from tortoise.models import Model



class Graphs(Model):
    ID = fields.IntField(pk=True, unique=True, generated=False)
    rawTitle = fields.TextField(null=False,pk=False, generated=False)
    POI_state = fields.TextField(null=True,pk=False, description="State that the POI is managed by", generated=False)
    POI_server = fields.TextField(null=True,pk=False, generated=False)
    POI_code = fields.CharField(4, unique=True,pk=False, null=True, generated=False)
    state = fields.TextField(null=True,pk=False, description="State the POI is based in", generated=False)
    NBN_CVC = fields.CharField(15, null=True, pk=False,unique=True, generated=False)
    CSA = fields.CharField(15, null=True, pk=False,unique=True, generated=False)
    VLink_Circuit_ID = fields.CharField(11,null=True,pk=False, unique=True, generated=False)
    max_bandwidth = fields.IntField(null=True,pk=False, generated=False)
    location = fields.TextField(null=True, pk=False, generated=False)
    OPTUS_CVC = fields.CharField(15, pk=False,null=True, unique=True, generated=False)
    AGVL = fields.TextField(null=True,pk=False, generated=False)
    Optus_STag = fields.IntField(null=True,pk=False, generated=False)
    NBN_STag = fields.IntField(null=True,pk=False, generated=False)
    VTag_VLAN_ID = fields.IntField(null=True,pk=False, generated=False)
    OON = fields.IntField(null=True,pk=False, generated=False)
    ORD_VLINK = fields.CharField(15,null=True,pk=False, generated=False)
    ORD_CVC = fields.CharField(15,null=True,pk=False, unique=True, generated=False)
    NNI_Link_ID = fields.CharField(15,null=True,pk=False, generated=False)
    VNNI_ID = fields.CharField(15,null=True,pk=False, generated=False)
    STAG_Ranges = fields.CharField(8,null=True, pk=False, generated=False)
    notes = fields.TextField(null=True,pk=False, generated=False)
    relation: fields.ReverseRelation["Transit"]


class Transit(Model):
    ID = fields.UUIDField(pk=True, unique=True)
    unique = (("DateTime", "graph"),)
    index = ("DateTime", "graph")
    graph: fields.ForeignKeyRelation[Graphs] = fields.ForeignKeyField("models.Graphs", related_name="relation")
    DateTime = fields.DatetimeField()
    Outbound = fields.FloatField(description="bps")
    Inbound = fields.FloatField(description="bps")
    Bandwidth = fields.FloatField(description="bps")
    Bandwidth_RoC = fields.FloatField(description="bps^2", null=True)


class ScrapeInfo(Model):
    datetime = fields.DatetimeField(pk=True, auto_now_add=True)
    noentries = fields.IntField()
    noentryfailed = fields.IntField()
    timetaken = fields.FloatField()
