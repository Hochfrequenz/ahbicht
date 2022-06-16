"""
Contains a class that is able to provide any RC/FC Evaluator, HintsProvider or Package Resolver.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from maus.edifact import EdifactFormat, EdifactFormatVersion

from ahbicht.content_evaluation.evaluators import Evaluator
from ahbicht.content_evaluation.fc_evaluators import FcEvaluator
from ahbicht.content_evaluation.rc_evaluators import RcEvaluator
from ahbicht.expressions.hints_provider import HintsProvider
from ahbicht.expressions.package_expansion import PackageResolver


class TokenLogicProvider(ABC):
    """
    A TokenLogicProvider is a class that can provide you with the correct evaluator/hints provider/package resolver
    for your use case/for any token in the parsed expression tree.
    """

    @abstractmethod
    def get_rc_evaluator(self, edifact_format: EdifactFormat, format_version: EdifactFormatVersion) -> RcEvaluator:
        """
        returns an appropriate RC Evaluator for the given edifact_format and edifact_format_version.
        The implementing class shall raise a NotImplementedError and not return None.
        """
        raise NotImplementedError("The inheriting sub class has to implement this method")

    @abstractmethod
    def get_fc_evaluator(self, edifact_format: EdifactFormat, format_version: EdifactFormatVersion) -> FcEvaluator:
        """
        returns an appropriate FC Evaluator for the given edifact_format and edifact_format_version.
        The implementing class shall raise a NotImplementedError and not return None.
        """
        raise NotImplementedError("The inheriting sub class has to implement this method")

    @abstractmethod
    def get_hints_provider(
        self, edifact_format: Optional[EdifactFormat] = None, format_version: Optional[EdifactFormatVersion] = None
    ) -> HintsProvider:
        """
        returns an appropriate HintsProvider for the given edifact_format and edifact_format_version.
        The implementing class shall raise a NotImplementedError and not return None.
        """
        raise NotImplementedError("The inheriting sub class has to implement this method")

    @abstractmethod
    def get_package_resolver(
        self, edifact_format: Optional[EdifactFormat] = None, format_version: Optional[EdifactFormatVersion] = None
    ) -> PackageResolver:
        """
        Returns an appropriate PackageResolver for the given edifact_format and edifact_format_version.
        You can provide None as format(version) if there is only 1 package resolver available
        The implementing class shall raise a NotImplementedError and not return None.
        """
        raise NotImplementedError("The inheriting sub class has to implement this method")


class SingletonTokenLogicProvider(TokenLogicProvider):
    """
    An TokenLogicProvider that is instantiated with a list of evaluators/providers/resolvers of which the same instances
    will be used during the entire uptime of the application (singleton style).
    """

    _unknown_key = "undefined"

    @staticmethod
    def _to_key(edifact_format: Optional[EdifactFormat], format_version: Optional[EdifactFormatVersion]) -> str:
        """
        because a tuple for format and format version is not hashable / usuable as key in a dict this methods
        converts them to a unique and hashable string
        """
        if edifact_format is None or format_version is None:
            return SingletonTokenLogicProvider._unknown_key
        # we don't care what the key is, it just has to be unique and consistent
        return f"{edifact_format}-{format_version}"

    def __init__(self, inputs: List[Union[Evaluator, PackageResolver, HintsProvider]]):
        self._rc_evaluators: Dict[str, RcEvaluator] = {}
        self._fc_evaluators: Dict[str, FcEvaluator] = {}
        self._hints_providers: Dict[str, HintsProvider] = {}
        self._package_resolvers: Dict[str, PackageResolver] = {}
        for instance in inputs:
            key: str
            try:
                key = SingletonTokenLogicProvider._to_key(instance.edifact_format, instance.edifact_format_version)
            except NotImplementedError:
                # this is ok, if there's only one of the kind (e.g. only one package resolver, only one hints provider)
                # if the user tries to provide more than 1 instance of the same kind without specifying format(version)
                # they'll run into an value error below
                key = SingletonTokenLogicProvider._unknown_key
            target_dict: Dict[str, Any]
            if isinstance(instance, RcEvaluator):
                target_dict = self._rc_evaluators
            elif isinstance(instance, FcEvaluator):
                target_dict = self._fc_evaluators
            elif isinstance(instance, HintsProvider):
                target_dict = self._hints_providers
            elif isinstance(instance, PackageResolver):
                target_dict = self._package_resolvers
            else:
                raise ValueError(f"The type of '{instance}' is not supported. Expected either RC or FC evaluator")
            if key in target_dict:
                conflict = target_dict[key]
                raise ValueError(
                    f"The key '{key}' is already used by {conflict}. For this reason you cannot add '{instance}'"
                )
            target_dict[key] = instance

    def get_fc_evaluator(
        self, edifact_format: Optional[EdifactFormat] = None, format_version: Optional[EdifactFormatVersion] = None
    ) -> FcEvaluator:
        try:
            return self._fc_evaluators[SingletonTokenLogicProvider._to_key(edifact_format, format_version)]
        except KeyError as key_error:
            raise NotImplementedError(
                f"No FC Evaluator has been registered for {edifact_format} in {format_version}"
            ) from key_error

    def get_rc_evaluator(
        self, edifact_format: Optional[EdifactFormat] = None, format_version: Optional[EdifactFormatVersion] = None
    ) -> RcEvaluator:
        try:
            return self._rc_evaluators[SingletonTokenLogicProvider._to_key(edifact_format, format_version)]
        except KeyError as key_error:
            raise NotImplementedError(
                f"No RC Evaluator has been registered for {edifact_format} in {format_version}"
            ) from key_error

    def get_hints_provider(
        self, edifact_format: Optional[EdifactFormat] = None, format_version: Optional[EdifactFormatVersion] = None
    ) -> HintsProvider:
        try:
            return self._hints_providers[SingletonTokenLogicProvider._to_key(edifact_format, format_version)]
        except KeyError as key_error:
            raise NotImplementedError(
                f"No HintsProvider has been registered for {edifact_format} in {format_version}"
            ) from key_error

    def get_package_resolver(
        self, edifact_format: Optional[EdifactFormat] = None, format_version: Optional[EdifactFormatVersion] = None
    ) -> PackageResolver:
        try:
            return self._package_resolvers[SingletonTokenLogicProvider._to_key(edifact_format, format_version)]
        except KeyError as key_error:
            raise NotImplementedError(
                f"No PackageResolver has been registered for {edifact_format} in {format_version}"
            ) from key_error
