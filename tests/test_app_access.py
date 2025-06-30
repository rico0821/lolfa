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
    print(f"Sidebar widgets: {at.sidebar}")
    print(f"Radio widgets: {at.radio}")
    # Try to set the sidebar radio to 'Admin Card Preview' if available
    if len(at.radio) > 0:
        at.radio[0].set_value("Admin Card Preview")
        at = at.run(timeout=30)
        # Check for header
        assert any("Admin Card Preview" in h.value for h in at.header), "Admin Card Preview header not found"
        # Check for card HTML (look for overall rating and stat labels)
        card_html_found = False
        for m in at.markdown:
            if "Attack" in m.value and "Defence" in m.value and "Stability" in m.value:
                card_html_found = True
                break
        assert card_html_found, "FIFA-style card HTML not rendered in Admin Card Preview"
        # Check that at least one card is available for selection
        assert at.selectbox[0].options, "No cards available for selection in Admin Card Preview"
    else:
        raise AssertionError("No radio widgets found in sidebar after initial run") 