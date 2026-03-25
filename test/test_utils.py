from src.utils import group_warnings


def test_group_warnings_groups_categories_and_preserves_freeform_messages():
    grouped = group_warnings(
        [
            "Title: Too short",
            "Title: Missing keyword",
            "No canonical tag found",
        ]
    )

    assert grouped["Title"] == ["Too short", "Missing keyword"]
    assert grouped["No canonical tag found"] == "No canonical tag found"
