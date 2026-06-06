from __future__ import annotations

from scriptweaver.domain.models import Uncertainty, UncertaintyResolution


class UncertaintyValidationError(ValueError):
    """Raised when uncertainty options or answers are invalid."""


def validate_uncertainties(uncertainties: list[Uncertainty]) -> None:
    for uncertainty in uncertainties:
        option_count = len(uncertainty.options)
        if option_count == 0:
            if not uncertainty.allow_custom_answer:
                raise UncertaintyValidationError(
                    f"Uncertainty {uncertainty.id} must allow a custom answer "
                    "when it has no options"
                )
            continue

        if not 2 <= option_count <= 4:
            raise UncertaintyValidationError(
                f"Uncertainty {uncertainty.id} must contain between 2 and 4 "
                "options"
            )

        seen_option_ids: set[str] = set()
        for option in uncertainty.options:
            if option.id in seen_option_ids:
                raise UncertaintyValidationError(
                    f"Uncertainty {uncertainty.id} contains duplicate option "
                    f"id: {option.id}"
                )
            seen_option_ids.add(option.id)


def validate_uncertainty_resolutions(
    uncertainties: list[Uncertainty],
    resolutions: list[UncertaintyResolution],
) -> None:
    uncertainty_by_id = {
        uncertainty.id: uncertainty for uncertainty in uncertainties
    }
    resolved_uncertainty_ids: set[str] = set()

    for resolution in resolutions:
        uncertainty = uncertainty_by_id.get(resolution.uncertainty_id)
        if uncertainty is None:
            raise UncertaintyValidationError(
                "Resolution references unknown uncertainty: "
                f"{resolution.uncertainty_id}"
            )

        if resolution.uncertainty_id in resolved_uncertainty_ids:
            raise UncertaintyValidationError(
                "Duplicate resolution for uncertainty: "
                f"{resolution.uncertainty_id}"
            )
        resolved_uncertainty_ids.add(resolution.uncertainty_id)

        has_selected_option = (
            resolution.selected_option_id is not None
            and bool(resolution.selected_option_id.strip())
        )
        has_custom_answer = (
            resolution.custom_answer is not None
            and bool(resolution.custom_answer.strip())
        )
        if has_selected_option == has_custom_answer:
            raise UncertaintyValidationError(
                f"Resolution for {resolution.uncertainty_id} must provide "
                "exactly one selected option or custom answer"
            )

        if has_selected_option:
            option_ids = {option.id for option in uncertainty.options}
            if resolution.selected_option_id not in option_ids:
                raise UncertaintyValidationError(
                    f"Resolution for {resolution.uncertainty_id} references "
                    f"unknown option: {resolution.selected_option_id}"
                )

        if has_custom_answer and not uncertainty.allow_custom_answer:
            raise UncertaintyValidationError(
                f"Uncertainty {uncertainty.id} does not allow a custom answer"
            )
