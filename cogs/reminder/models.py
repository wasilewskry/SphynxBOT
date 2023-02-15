from tortoise import fields
from tortoise.models import Model

from cogs.reminder.helpers import ReminderType


class Reminder(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User')
    guild_id = fields.BigIntField(null=True)
    channel_id = fields.BigIntField(null=True)
    reminder_type = fields.IntEnumField(ReminderType)
    target_time = fields.DatetimeField()
    description = fields.CharField(2048)
