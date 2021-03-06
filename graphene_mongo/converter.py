from graphene import (ID, Boolean, Dynamic, Field, Float, Int, List,
                      NonNull, String, is_node)
from graphene.types.json import JSONString

import mongoengine

from .fields import MongoengineConnectionField
from .utils import import_single_dispatch

singledispatch = import_single_dispatch()


@singledispatch
def convert_mongoengine_field(field, registry=None):
    raise Exception(
        "Don't know how to convert the MongoEngine field %s (%s)" %
        (field, field.__class__))


@convert_mongoengine_field.register(mongoengine.EmailField)
@convert_mongoengine_field.register(mongoengine.StringField)
@convert_mongoengine_field.register(mongoengine.URLField)
def convert_field_to_string(field, registry=None):
    return String(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.UUIDField)
@convert_mongoengine_field.register(mongoengine.ObjectIdField)
def convert_field_to_id(field, registry=None):
    return ID(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.IntField)
def convert_field_to_int(field, registry=None):
    return Int(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.BooleanField)
def convert_field_to_boolean(field, registry=None):
    return NonNull(Boolean, description=field.db_field)


@convert_mongoengine_field.register(mongoengine.DecimalField)
@convert_mongoengine_field.register(mongoengine.FloatField)
def convert_field_to_float(field, registry=None):
    return Float(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.DictField)
@convert_mongoengine_field.register(mongoengine.MapField)
def convert_dict_to_jsonstring(field, registry=None):
    return JSONString(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.DateTimeField)
def convert_date_to_string(field, registry=None):
    return String(description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.ListField)
def convert_postgres_array_to_list(field, registry=None):
    base_type = convert_mongoengine_field(field.field, registry=registry)
    if isinstance(base_type, (Dynamic)):
        base_type = base_type.get_type()._type
    if is_node(base_type):
        return MongoengineConnectionField(base_type)
    elif not isinstance(base_type, (List, NonNull)) \
            and not isinstance(field.field, mongoengine.ReferenceField):
        base_type = type(base_type)
    return List(base_type, description=field.db_field, required=not field.null)


@convert_mongoengine_field.register(mongoengine.EmbeddedDocumentField)
@convert_mongoengine_field.register(mongoengine.ReferenceField)
def convert_field_to_dynamic(field, registry=None):
    model = field.document_type

    def dynamic_type():
        _type = registry.get_type_for_model(model)
        if not _type:
            return None

        return Field(_type)

    return Dynamic(dynamic_type)
