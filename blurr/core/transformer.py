from typing import Dict, Type

from abc import ABC

from blurr.core.base import BaseItemCollection, BaseSchemaCollection, BaseItem
from blurr.core.data_group import DataGroup
from blurr.core.errors import MissingAttributeError
from blurr.core.evaluation import Context, EvaluationContext
from blurr.core.loader import TypeLoader
from blurr.core.schema_loader import SchemaLoader
from blurr.core.store import Store


class TransformerSchema(BaseSchemaCollection, ABC):
    """
    All Transformer Schema inherit from this base.  Adds support for handling
    the required attributes of a schema.
    """

    ATTRIBUTE_VERSION = 'Version'
    ATTRIBUTE_DESCRIPTION = 'Description'
    ATTRIBUTE_STORES = 'Stores'
    ATTRIBUTE_DATA_GROUPS = 'DataGroups'
    ATTRIBUTE_IMPORT = 'Import'
    ATTRIBUTE_IMPORT_MODULE = 'Module'
    ATTRIBUTE_IMPORT_IDENTIFIER = 'Identifier'

    def __init__(self, fully_qualified_name: str, schema_loader: SchemaLoader) -> None:
        super().__init__(fully_qualified_name, schema_loader, self.ATTRIBUTE_DATA_GROUPS)

        # Load the schema specific attributes
        self.version = self._spec[self.ATTRIBUTE_VERSION]
        self.description = self._spec[
            self.ATTRIBUTE_DESCRIPTION] if self.ATTRIBUTE_DESCRIPTION in self._spec else None

        # Load list of stores from the schema
        self.stores: Dict[str, Type[Store]] = {
            schema_spec[self.ATTRIBUTE_NAME]: self.schema_loader.get_nested_schema_object(
                self.fully_qualified_name, schema_spec[self.ATTRIBUTE_NAME])
            for schema_spec in self._spec.get(self.ATTRIBUTE_STORES, [])
        }

        self.import_list = self._spec[
            self.ATTRIBUTE_IMPORT] if self.ATTRIBUTE_IMPORT in self._spec else None
        self.schema_context = EvaluationContext()
        self.import_modules()

    def import_modules(self) -> None:
        if self.import_list is None:
            return

        for custom_import in self.import_list:
            module = custom_import[self.ATTRIBUTE_IMPORT_MODULE]
            module_obj = TypeLoader.import_by_full_name(module)
            if self.ATTRIBUTE_IMPORT_IDENTIFIER not in custom_import:
                self.schema_context.global_add(module, module_obj)
                return

            for identifier in custom_import[self.ATTRIBUTE_IMPORT_IDENTIFIER]:
                self.schema_context.global_add(identifier, getattr(module_obj, identifier))


class Transformer(BaseItemCollection, ABC):
    """
    All transformers inherit from this base.  Adds the current transformer
    to the context
    """

    def __init__(self, schema: TransformerSchema, identity: str) -> None:
        super().__init__(schema, schema.schema_context)
        # Load the nested items into the item
        self._data_groups: Dict[str, DataGroup] = {
            name: TypeLoader.load_item(item_schema.type)(item_schema, identity,
                                                         self._evaluation_context)
            for name, item_schema in schema.nested_schema.items()
        }
        self._identity = identity
        self._evaluation_context.global_add('identity', self._identity)
        self._evaluation_context.global_context.merge(self._nested_items)

    @property
    def _nested_items(self) -> Dict[str, DataGroup]:
        """
        Dictionary of nested data groups
        """
        return self._data_groups

    def finalize(self) -> None:
        """
        Iteratively finalizes all data groups in its transformer
        """
        for item in self._nested_items.values():
            item.finalize()

    def __getattr__(self, item: str) -> DataGroup:
        """
        Makes the value of the nested items available as properties
        of the collection object.  This is used for retrieving data groups
        for dynamic execution.
        :param item: Data group requested
        """
        return self.__getitem__(item)

    def __getitem__(self, item) -> DataGroup:
        """
        Makes the nested items available though the square bracket notation.
        :raises KeyError: When a requested item is not found in nested items
        """
        if item not in self._nested_items:
            raise MissingAttributeError('{item} not defined in {name}'.format(
                item=item, name=self._name))

        return self._nested_items[item]
