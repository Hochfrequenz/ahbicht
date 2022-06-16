from typing import List

import pytest  # type:ignore[import]
from _pytest.fixtures import SubRequest  # type:ignore[import]
from maus.edifact import EdifactFormat, EdifactFormatVersion

from ahbicht.content_evaluation.evaluators import Evaluator
from ahbicht.content_evaluation.fc_evaluators import FcEvaluator
from ahbicht.content_evaluation.rc_evaluators import RcEvaluator
from ahbicht.content_evaluation.token_logic_provider import SingletonTokenLogicProvider, TokenLogicProvider


class TestEvaluatorProvider:
    """
    Test that the list based evalutor provider works as expected
    """

    def test_initialization(self):
        evaluators: List[Evaluator] = []
        # setup some test data/instances
        for edifact_format in EdifactFormat:
            if edifact_format == EdifactFormat.COMDIS:
                # we use the comdis format to test the "not found"/not implemented case below
                continue
            for edifact_format_version in EdifactFormatVersion:

                class ExampleRcEvaluator(RcEvaluator):
                    def _get_default_context(self):
                        return None

                    def __init__(self):
                        super().__init__()
                        self.edifact_format_version = edifact_format_version
                        self.edifact_format = edifact_format

                class ExampleFcEvaluator(FcEvaluator):
                    def __init__(self):
                        super().__init__()
                        self.edifact_format_version = edifact_format_version
                        self.edifact_format = edifact_format

                example_rc_evaluator = ExampleRcEvaluator()
                example_fc_evaluator = ExampleFcEvaluator()
                evaluators.append(example_rc_evaluator)
                evaluators.append(example_fc_evaluator)
        # here's where the setup is over and the actual test begins
        evaluator_provider: TokenLogicProvider = SingletonTokenLogicProvider(evaluators)
        for edifact_format in EdifactFormat:
            for edifact_format_version in EdifactFormatVersion:
                if edifact_format == EdifactFormat.COMDIS:
                    # comdis is not set up (see above)
                    with pytest.raises(NotImplementedError):
                        _ = evaluator_provider.get_fc_evaluator(edifact_format, edifact_format_version)
                    with pytest.raises(NotImplementedError):
                        _ = evaluator_provider.get_rc_evaluator(edifact_format, edifact_format_version)
                    continue
                fc_evaluator = evaluator_provider.get_fc_evaluator(edifact_format, edifact_format_version)
                rc_evaluator = evaluator_provider.get_rc_evaluator(edifact_format, edifact_format_version)
                assert isinstance(fc_evaluator, FcEvaluator)
                assert isinstance(rc_evaluator, RcEvaluator)
                assert fc_evaluator.edifact_format_version == edifact_format_version
                assert fc_evaluator.edifact_format == edifact_format
                assert rc_evaluator.edifact_format_version == edifact_format_version
                assert rc_evaluator.edifact_format == edifact_format
