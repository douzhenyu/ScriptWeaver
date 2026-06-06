from dataclasses import replace

import pytest

from scriptweaver.domain.models import (
    Uncertainty,
    UncertaintyOption,
    UncertaintyResolution,
)
from scriptweaver.domain.uncertainty_validation import (
    UncertaintyValidationError,
    validate_uncertainties,
    validate_uncertainty_resolutions,
)


def make_option(option_id: str) -> UncertaintyOption:
    return UncertaintyOption(
        id=option_id,
        label=f"选项 {option_id}",
        description=f"描述 {option_id}",
        impact=f"影响 {option_id}",
    )


def make_uncertainty(
    uncertainty_id: str = "uncertainty_001",
    option_ids: tuple[str, ...] = ("option_001", "option_002"),
    allow_custom_answer: bool = True,
) -> Uncertainty:
    return Uncertainty(
        id=uncertainty_id,
        question="沈微是否提前知情？",
        context="答案影响人物动机。",
        options=[make_option(option_id) for option_id in option_ids],
        allow_custom_answer=allow_custom_answer,
        source_chapter_indexes=[1, 2],
    )


# ---- Question-validation tests ----

@pytest.mark.parametrize(
    "uncertainty",
    [
        make_uncertainty(option_ids=("option_001", "option_002")),
        make_uncertainty(allow_custom_answer=False),
        make_uncertainty(
            option_ids=("option_001", "option_002", "option_003", "option_004")
        ),
        make_uncertainty(option_ids=()),
    ],
)
def test_validate_uncertainties_accepts_answerable_questions(uncertainty):
    validate_uncertainties([uncertainty])


@pytest.mark.parametrize(
    ("uncertainty", "message"),
    [
        (
            make_uncertainty(option_ids=("option_001",)),
            "must contain between 2 and 4 options",
        ),
        (
            make_uncertainty(
                option_ids=(
                    "option_001",
                    "option_002",
                    "option_003",
                    "option_004",
                    "option_005",
                )
            ),
            "must contain between 2 and 4 options",
        ),
        (
            make_uncertainty(option_ids=(), allow_custom_answer=False),
            "must allow a custom answer when it has no options",
        ),
        (
            make_uncertainty(option_ids=("option_001", "option_001")),
            "contains duplicate option id: option_001",
        ),
    ],
)
def test_validate_uncertainties_rejects_invalid_questions(
    uncertainty,
    message,
):
    with pytest.raises(UncertaintyValidationError, match=message):
        validate_uncertainties([uncertainty])


def test_validate_uncertainties_allows_reused_option_ids_across_questions():
    validate_uncertainties(
        [
            make_uncertainty("uncertainty_001"),
            make_uncertainty("uncertainty_002"),
        ]
    )


# ---- Answer-validation tests ----


def test_validate_uncertainty_resolutions_accepts_empty_and_partial_answers():
    uncertainties = [
        make_uncertainty("uncertainty_001"),
        make_uncertainty("uncertainty_002"),
    ]

    validate_uncertainty_resolutions(uncertainties, [])
    validate_uncertainty_resolutions(
        uncertainties,
        [
            UncertaintyResolution(
                uncertainty_id="uncertainty_001",
                selected_option_id="option_001",
            )
        ],
    )


def test_validate_uncertainty_resolutions_accepts_custom_answer():
    validate_uncertainty_resolutions(
        [make_uncertainty()],
        [
            UncertaintyResolution(
                uncertainty_id="uncertainty_001",
                custom_answer="沈微只知道密信存在。",
            )
        ],
    )


@pytest.mark.parametrize(
    ("uncertainties", "resolutions", "message"),
    [
        (
            [make_uncertainty()],
            [
                UncertaintyResolution(
                    uncertainty_id="uncertainty_999",
                    selected_option_id="option_001",
                )
            ],
            "references unknown uncertainty: uncertainty_999",
        ),
        (
            [make_uncertainty()],
            [
                UncertaintyResolution(
                    uncertainty_id="uncertainty_001",
                    selected_option_id="option_001",
                ),
                UncertaintyResolution(
                    uncertainty_id="uncertainty_001",
                    selected_option_id="option_002",
                ),
            ],
            "Duplicate resolution for uncertainty: uncertainty_001",
        ),
        (
            [make_uncertainty()],
            [
                UncertaintyResolution(
                    uncertainty_id="uncertainty_001",
                    selected_option_id="option_999",
                )
            ],
            "references unknown option: option_999",
        ),
        (
            [make_uncertainty(allow_custom_answer=False)],
            [
                UncertaintyResolution(
                    uncertainty_id="uncertainty_001",
                    custom_answer="自定义答案",
                )
            ],
            "does not allow a custom answer",
        ),
        (
            [make_uncertainty()],
            [
                UncertaintyResolution(
                    uncertainty_id="uncertainty_001",
                    selected_option_id="option_001",
                    custom_answer="自定义答案",
                )
            ],
            "must provide exactly one",
        ),
        (
            [make_uncertainty()],
            [UncertaintyResolution(uncertainty_id="uncertainty_001")],
            "must provide exactly one",
        ),
        (
            [make_uncertainty()],
            [
                UncertaintyResolution(
                    uncertainty_id="uncertainty_001",
                    selected_option_id=" option_001 ",
                )
            ],
            "references unknown option:  option_001 ",
        ),
    ],
)
def test_validate_uncertainty_resolutions_rejects_invalid_answers(
    uncertainties,
    resolutions,
    message,
):
    with pytest.raises(UncertaintyValidationError, match=message):
        validate_uncertainty_resolutions(uncertainties, resolutions)


@pytest.mark.parametrize(
    ("selected_option_id", "custom_answer"),
    [
        ("", None),
        (" \n ", None),
        (None, ""),
        (None, "\t"),
        (" ", "\n"),
    ],
)
def test_validate_uncertainty_resolutions_treats_blank_values_as_absent(
    selected_option_id,
    custom_answer,
):
    resolution = UncertaintyResolution(
        uncertainty_id="uncertainty_001",
        selected_option_id=selected_option_id,
        custom_answer=custom_answer,
    )

    with pytest.raises(UncertaintyValidationError, match="must provide exactly one"):
        validate_uncertainty_resolutions([make_uncertainty()], [resolution])


def test_uncertainty_validators_are_public_domain_exports():
    from scriptweaver.domain import (
        UncertaintyValidationError as ExportedUncertaintyValidationError,
        validate_uncertainties as exported_validate_uncertainties,
        validate_uncertainty_resolutions as exported_validate_resolutions,
    )

    assert ExportedUncertaintyValidationError is UncertaintyValidationError
    assert exported_validate_uncertainties is validate_uncertainties
    assert exported_validate_resolutions is validate_uncertainty_resolutions
