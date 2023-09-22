import logging
import re
from types import MappingProxyType
from typing import List, Mapping, Tuple

logger = logging.getLogger(__name__)


class InstrumentMethod:
    """
    Generic instrument mehtod class that can be used for any Empower instrument method.
    For specific instrument methods, a subclass should be created that inherits from
    this class.

    Specific parameters for the method can be set and retrieved using the [] operator,
    e.g `method["ColumnTemperature"] = "50.03"`. This will replace the current value of
    ColumnTemperature with the new value in the underlying xml. The current value can be
    retrieved in the same way. This only works if there is exactly one instance of the
    key in the xml. If there are multiple instances, a ValueError will be raised. If the
    key is not present, a KeyError will be raised. If more than one key is present, use
    the xml key to retrieve the xml and make changes to it through the `replace` method.
    This will replace all instances of the original string with the new string in the
    xml.

    If no xml key is present in the method definition, no changes can be made to the
    method, but the original method definition can still be retrieved.

    :attribute original_method: The original method definition.
    :attribute current_method: The current method definition, including the changes that
        have been made.
    """

    def __init__(self, method_definition: Mapping[str, str]):
        """
        Initialize the InstrumentMethod.

        :param method_definition: The method definition from Empower. Should contain at
            least an xml key. If it is not present, the InstrumentMethod can still be
            created, but no changes can be made to the method, and no values can be
            extracted.
        """
        self.original_method = MappingProxyType(method_definition)
        self._change_list: List[Tuple[str, str]] = []

    def replace(self, original: str, new: str) -> None:
        """
        Replace all instances of a string in the xml of the current method.

        :param original: The string to replace.
        :param new: The string to replace it with.
        """
        self._change_list.append((original, new))

    # If this property method is called often, there could be performance issues. In
    # that case, consider cahcing the result with `@functools.lru_cahce(maxsize=1)`. You
    # also need to implement a `__hash__` method and an `__eq__` method for this to
    # work.
    @property
    def current_method(self) -> Mapping[str, str]:
        """The current method definition, including the changes that have been made."""
        logger.debug("Applying changes to create current method")
        return self.alter_method(self.original_method, self._change_list)

    def __getitem__(self, key: str) -> str:
        try:
            xml = self.current_method["xml"]
        except KeyError as ex:
            raise KeyError("No xml found in method definition") from ex
        search_result = re.search(f"<{key}>(.*)</{key}>", xml)
        if not search_result:
            raise KeyError(f"Could not find key {key}")
        if f"<{key}>" in search_result.groups(1)[0]:
            # Python regex returns the maximum match, so if the key is found multiple
            # times, it will return everything between the first opening tag and the
            # last closing tag. This is not what we want, so we raise an error if this
            # happens.
            raise ValueError(f"Found more than one match for key {key}")
        return search_result.groups(1)[0]

    def __setitem__(self, key: str, value: str) -> None:
        current_value = self[key]
        self.replace(f"<{key}>{current_value}</{key}>", f"<{key}>{value}</{key}>")

    @staticmethod
    def alter_method(
        original_method: Mapping[str, str], change_list: List[Tuple[str, str]]
    ) -> Mapping[str, str]:
        """
        Alter the a method definition by applying the changes in the change list.
        """
        method = dict(original_method)
        try:
            xml: str = method["xml"]
        except KeyError as ex:
            if len(change_list) > 0:
                raise ValueError(
                    "Cannot apply changes to method, no xml key in method definition."
                ) from ex
            else:
                # If there is no xml key, we can't do anything with the method. But if
                # there are no changes to apply, we can just return the original method.
                return method
        for original, new in change_list:
            logger.debug("Replacing %s with %s", original, new)
            num_replaced = xml.count(original)
            if num_replaced == 0:
                logger.warning(
                    f"Could not find {original} in {method}, no changes made to method."
                )  # Consider trying to replace `<` with `&lt` aand `>` with `&gt;` and
                # then trying again.
            else:
                xml = xml.replace(original, new)
                logger.debug(
                    "Replaced %s instances of %s with %s", num_replaced, original, new
                )
        method["xml"] = xml
        return method


class ColumnHandler(InstrumentMethod):
    """
    Class for instrument methods that have a column temperature.

    :attribute column_temperature: The column temperature.
    """

    temperature_key: str

    @property
    def column_temperature(self):
        return self[self.temperature_key]

    @column_temperature.setter
    def column_temperature(self, value: str) -> None:
        self[self.temperature_key] = value


class SampleManager(ColumnHandler):
    """Class for instrument methods that control a sample manager."""

    temperature_key = "ColumnTemperature"


def instrument_method_factory(method_definition: Mapping[str, str]) -> InstrumentMethod:
    """
    Factory function for creating an InstrumentMethod from a method definition. The
    method definition should contain at least a name key, which is used to determine
    which subclass of InstrumentMethod should be created. If the name key is not present
    or the name is not recognized, a generic InstrumentMethod will be created.
    """
    try:
        if method_definition["name"] in ["rAcquityFTN"]:
            logger.debug("Creating SampleManager")
            return SampleManager(method_definition)
        # Add more cases as they are coded
        else:
            logger.debug(
                "Unknown instrument method: %s, creating a generic InstrumentMethod",
                method_definition["name"],
            )  # The error is always caught, so we use the debug level here.
            raise ValueError(f"Unknown instrument method: {method_definition['name']}")
    except (KeyError, ValueError) as e:
        if isinstance(e, KeyError):
            # If the name key is not present, we don't know what to do with it, but we
            # can still create a generic InstrumentMethod and just return that.
            logger.debug("KeyError: %s, creating a generic InstrumentMethod", e)
        return InstrumentMethod(method_definition)
