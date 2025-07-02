import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from streamlit.testing.v1 import AppTest

def test_app_accessible():
    at = AppTest.from_file("app.py")
    try:
        at = at.run(timeout=30)
    except Exception as e:
        pytest.fail(f"AppTest failed to run: {e}")
    # Ensure the app rendered at least one UI element
    if not at.title and not at.error and not at.warning and not at.markdown and not at.header:
        pytest.fail("App did not render any UI elements (possible crash or early exit)")
    # Check for error messages in the UI
    error_blocks = [e.value for e in at.error]
    assert not error_blocks, f"App rendered error(s): {error_blocks}"
    # Check the title is present
    assert any("LoL eSports Player Card" in t.value for t in at.title), "App title not found"

def test_admin_card_preview_accessible():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file("app.py")
    at = at.run(timeout=30)
    # Set the sidebar radio to 'Admin Card Preview'
    radio_widgets = [r for r in at.radio if r.label == 'Select Page']
    assert radio_widgets, "Sidebar radio for tab selection not found"
    radio_widgets[0].set_value("Admin Card Preview")
    at = at.run(timeout=30)
    # Select the first available card id in the selectbox
    selectboxes = [s for s in at.selectbox if s.label == 'Select card']
    assert selectboxes, "Card selectbox not found in Admin Card Preview"
    first_option = selectboxes[0].options[0]
    selectboxes[0].set_value(first_option)
    at = at.run(timeout=30)
    # Check for header
    assert any("Admin Card Preview" in h.value for h in at.header), "Admin Card Preview header not found"
    # Check for card HTML (look for player name in the HTML)
    card_html_found = False
    for m in at.markdown:
        if str(first_option) in m.value or "Player" in m.value:
            card_html_found = True
            break
    assert card_html_found, "Card HTML not rendered for selected card" 