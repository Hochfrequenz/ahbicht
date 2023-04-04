import pytest  # type:ignore[import]
from maus.models.edifact_components import DataElementDataType

from ahbicht.validation.validation_results import (
    DataElementValidationResult,
    ListOfValidationResultInContext,
    SegmentLevelValidationResult,
    ValidationResultInContext,
)
from ahbicht.validation.validation_values import RequirementValidationValue

# lovric = list_of_validation_result_in_context


class TestValidationResults:
    @pytest.mark.parametrize(
        "lovric_actual, edi_seed_to_bo4e_mappings, lovric_expected",
        [
            pytest.param(
                ListOfValidationResultInContext(
                    validation_results=[
                        ValidationResultInContext(
                            discriminator="$['Transaktionsgrund']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_FORBIDDEN_AND_EMPTY, hints="foo"
                            ),
                        ),
                        ValidationResultInContext(
                            discriminator="$['EdiFoo']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_REQUIRED, hints="bar"
                            ),
                        ),
                    ],
                ),
                {
                    "$['Transaktionsgrund']": "$['transaktionsdaten']['transaktionsgrund']",
                    "$['EdiFoo']": "$['stammdaten'][0]['applicationFoo']",
                },
                ListOfValidationResultInContext(
                    validation_results=[
                        ValidationResultInContext(
                            discriminator="$['transaktionsdaten']['transaktionsgrund']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_FORBIDDEN_AND_EMPTY, hints="foo"
                            ),
                        ),
                        ValidationResultInContext(
                            discriminator="$['stammdaten'][0]['applicationFoo']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_REQUIRED, hints="bar"
                            ),
                        ),
                    ],
                ),
            ),
        ],
    )
    async def test_lovric_replace_edi_seed_paths_with_bo4e_paths(
        self,
        lovric_actual: ListOfValidationResultInContext,
        edi_seed_to_bo4e_mappings: dict,
        lovric_expected: ListOfValidationResultInContext,
    ):
        lovric_actual.replace_edi_domain_paths_with_application_domain_paths(edi_seed_to_bo4e_mappings)
        assert lovric_actual == lovric_expected

    @pytest.mark.parametrize(
        "lovric_actual, lovric_expected",
        [
            pytest.param(
                ListOfValidationResultInContext(
                    validation_results=[
                        ValidationResultInContext(
                            discriminator="SG11",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_REQUIRED
                            ),
                        ),
                        ValidationResultInContext(
                            discriminator="SG11 - Datum",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_REQUIRED
                            ),
                        ),
                        ValidationResultInContext(
                            discriminator="SG11 - Datum - Auszug",
                            validation_result=DataElementValidationResult(
                                requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                                format_validation_fulfilled=True,
                                data_element_data_type=DataElementDataType.DATETIME,
                            ),
                        ),
                        ValidationResultInContext(
                            discriminator="SG10 - Datum",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_REQUIRED
                            ),
                        ),
                        ValidationResultInContext(
                            discriminator="SG10 - Datum - Einzug",
                            validation_result=DataElementValidationResult(
                                requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                                format_validation_fulfilled=True,
                                data_element_data_type=DataElementDataType.DATETIME,
                            ),
                        ),
                    ],
                ),
                ListOfValidationResultInContext(
                    validation_results=[
                        ValidationResultInContext(
                            discriminator="SG11 - Datum - Auszug",
                            validation_result=DataElementValidationResult(
                                requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                                format_validation_fulfilled=True,
                                data_element_data_type=DataElementDataType.DATETIME,
                            ),
                        ),
                        ValidationResultInContext(
                            discriminator="SG10 - Datum - Einzug",
                            validation_result=DataElementValidationResult(
                                requirement_validation=RequirementValidationValue.IS_REQUIRED_AND_EMPTY,
                                format_validation_fulfilled=True,
                                data_element_data_type=DataElementDataType.DATETIME,
                            ),
                        ),
                    ],
                ),
            ),
        ],
    )
    async def test_lovric_filter_for_data_element_validation_results(
        self, lovric_actual: ListOfValidationResultInContext, lovric_expected: ListOfValidationResultInContext
    ):
        lovric_actual.filter_for_data_element_validation_results()
        assert lovric_actual == lovric_expected

    @pytest.mark.parametrize(
        "lovric_actual, lovric_expected",
        [
            pytest.param(
                ListOfValidationResultInContext(
                    validation_results=[
                        ValidationResultInContext(
                            discriminator="$['Transaktionsgrund']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_FORBIDDEN_AND_EMPTY, hints="foo"
                            ),
                        ),
                        ValidationResultInContext(
                            discriminator="$['transaktionsdaten']['transaktionsgrund']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_FORBIDDEN_AND_EMPTY, hints="foo"
                            ),
                        ),
                        ValidationResultInContext(
                            discriminator="$['stammdaten'][0]['applicationFoo']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_REQUIRED, hints="bar"
                            ),
                        ),
                        ValidationResultInContext(
                            discriminator="$['EdiFoo']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_REQUIRED, hints="bar"
                            ),
                        ),
                    ],
                ),
                ListOfValidationResultInContext(
                    validation_results=[
                        ValidationResultInContext(
                            discriminator="$['transaktionsdaten']['transaktionsgrund']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_FORBIDDEN_AND_EMPTY, hints="foo"
                            ),
                        ),
                        ValidationResultInContext(
                            discriminator="$['stammdaten'][0]['applicationFoo']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_REQUIRED, hints="bar"
                            ),
                        ),
                    ],
                ),
            ),
        ],
    )
    async def test_lovric_filter_for_boneycomb_path_results(
        self, lovric_actual: ListOfValidationResultInContext, lovric_expected: ListOfValidationResultInContext
    ):
        lovric_actual.filter_for_boneycomb_path_results()
        assert lovric_actual == lovric_expected

    @pytest.mark.parametrize(
        "lovric_actual, lovric_expected",
        [
            pytest.param(
                ListOfValidationResultInContext(
                    validation_results=[
                        ValidationResultInContext(
                            discriminator='$["stammdaten"]["MARKTTEILNEHMER"]["ANSPRECHPARTNER"]["absender"]["ansprechpartner"]["nachname"]',
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_FORBIDDEN_AND_EMPTY, hints="foo"
                            ),
                        ),
                        ValidationResultInContext(
                            discriminator="$['transaktionsdaten']['transaktionsgrund']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_FORBIDDEN_AND_EMPTY, hints="foo"
                            ),
                        ),
                        ValidationResultInContext(
                            discriminator="$['stammdaten'][0]['applicationFoo']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_REQUIRED, hints="bar"
                            ),
                        ),
                        ValidationResultInContext(
                            discriminator='$["stammdaten"]["MARKTTEILNEHMER"]["empfaenger"]["rollencodenummer"]',
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_REQUIRED, hints="bar"
                            ),
                        ),
                    ],
                ),
                ListOfValidationResultInContext(
                    validation_results=[
                        ValidationResultInContext(
                            discriminator="$['transaktionsdaten']['transaktionsgrund']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_FORBIDDEN_AND_EMPTY, hints="foo"
                            ),
                        ),
                        ValidationResultInContext(
                            discriminator="$['stammdaten'][0]['applicationFoo']",
                            validation_result=SegmentLevelValidationResult(
                                requirement_validation=RequirementValidationValue.IS_REQUIRED, hints="bar"
                            ),
                        ),
                    ],
                ),
            ),
        ],
    )
    async def test_lovric_remove_absender_and_empfaenger_path_results(
        self, lovric_actual: ListOfValidationResultInContext, lovric_expected: ListOfValidationResultInContext
    ):
        lovric_actual.remove_absender_and_empfaenger_path_results()  # type:ignore[attr-defined]
        assert lovric_actual == lovric_expected
