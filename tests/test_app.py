from streamlit.testing.v1 import AppTest
import pytest

def test_app_initial_render():
    at = AppTest.from_file("app.py")
    
    at.session_state["disclaimer_acknowledged"] = True
    
    at.run()
    
    # Check if the main title is rendered
    assert not at.exception
    
    # Check if the text exists in the main container
    found_text = False
    for element in at.main:
        # hasattr check ensures we don't crash on buttons or other non-text elements
        if hasattr(element, 'value'):
            if "Full-text Paper Screener" in str(element.value):
                found_text = True
                break
    
    assert found_text, "Could not find 'Full-text Paper Screener' in the app"

def test_screener_mode_selection():
    at = AppTest.from_file("app.py").run()
    
    # Skip disclaimer (Set state)
    at.session_state["disclaimer_acknowledged"] = True 
    at.run()
    
    # Click the screener button
    at.button(key="screener_btn").click().run()
    
    # Check if we switched to screener mode
    assert at.session_state["app_mode"] == "screener"