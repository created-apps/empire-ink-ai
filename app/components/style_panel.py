"""
Mughal style preset selector panel.
Used on both the Generate and Transform tabs.
Returns a reactive NiceGUI select element.
"""

from nicegui import ui

PRESET_INFO = {
    "akbari": {
        "label": "Akbari (1556–1605)",
        "description": "Bold outlines · Jewel tones · Persian fusion · Rich compositions",
        "color": "#8B1A1A",
    },
    "jahangiri": {
        "label": "Jahangiri (1605–1627)",
        "description": "Naturalistic detail · Pastel palette · Gold leaf borders · Fine brushwork",
        "color": "#B8860B",
    },
    "shahjahani": {
        "label": "Shahjahani (1628–1658)",
        "description": "Marble aesthetic · Refined symmetry · Ivory & gold · Floral borders",
        "color": "#2E5875",
    },
}


def style_panel(current_value: str = "akbari") -> ui.select:
    """
    Renders the Mughal style preset selector with descriptions.

    Args:
        current_value: Initially selected preset key.

    Returns:
        The ui.select element (bind .value for reactive access).
    """
    with ui.column().classes("w-full gap-2"):
        ui.label("Mughal Art Style").classes("ei-section-label")

        style_select = ui.select(
            options={k: v["label"] for k, v in PRESET_INFO.items()},
            value=current_value,
            label="Choose an era",
        ).classes("w-full ei-select")

        # Description card that updates with selection
        desc_label = ui.label(PRESET_INFO[current_value]["description"]).classes(
            "text-sm opacity-70 italic px-1"
        )

        def on_change(e):
            key = e.value
            if key in PRESET_INFO:
                desc_label.text = PRESET_INFO[key]["description"]

        style_select.on_value_change(on_change)

    return style_select
