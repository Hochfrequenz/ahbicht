import inject
import pytest
import pytest_asyncio

from unittests.defaults import EmptyDefaultRcEvaluator


class SomethingInjectable:
    """
    This class is used by the custom Evaluators below
    """


class RcEvaluatorThatUsesInjectAttr(EmptyDefaultRcEvaluator):
    # this won't work and the test proves it
    something_injectable: SomethingInjectable = inject.attr(SomethingInjectable)


class TestErrorWhenUsingInjectAttr:
    """
    Asserts on a specific error message when a library user tries to use inject.attr
    """

    @pytest_asyncio.fixture()
    def clear_injectors(self):
        # This might not be necessary when you only run this test alone but without this fixture
        # running all the tests (e.g. via tox) might fail
        inject.clear()

    def test_attribute_error_with_inject_attr(self, clear_injectors):
        """
        This tests that an error with a meaningful error message is raised.
        Test can be removed as soon as the underlying bug in inject is resolved.
        """
        with pytest.raises(AttributeError) as attribute_error:
            RcEvaluatorThatUsesInjectAttr()
        assert (
            "Using inject.attr in custom evaluators as you tried in RcEvaluatorThatUsesInjectAttr is not supported."
            in str(attribute_error)
        )
