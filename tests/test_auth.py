import pytest
import re
from playwright.sync_api import Page, expect
from django.contrib.auth.models import User
from recipes.models import Recipe
from qase.pytest import qase

# Apply the database mark to all tests in this file so they can interact with the DB
pytestmark = pytest.mark.django_db

@qase.id(22)
def test_should_create_account_successfully_when_valid_registration_data_is_submitted(page: Page, live_server):
    """
    Test successful registration flow with valid credentials using exact IDs.
    """
    page.goto(f"{live_server.url}/register/")

    # Action: Fill registration form using strict Django auto-generated IDs
    page.locator("#id_username").fill("newautomationuser")
    page.locator("#id_email").fill("newuser@isharerecipe.com")
    page.locator("#id_password1").fill("SecurePass123!")
    page.locator("#id_password2").fill("SecurePass123!")

    page.get_by_role("button", name="Create Account").click()

    # Assertion: Should redirect to Home page safely
    expect(page).to_have_url(re.compile(rf"^{re.escape(live_server.url)}/?$"))

    # Assertion: User should be logged in automatically (Avatar dropdown visible exactly once)
    user_dropdown = page.locator("#userDropdown")
    expect(user_dropdown).to_have_count(1)
    expect(user_dropdown).to_be_visible()

    # Validation: Ensure user was actually created in database
    assert User.objects.filter(username="newautomationuser").exists()

@qase.id(23)
def test_should_reject_registration_when_password_and_confirm_password_do_not_match(page: Page, live_server):
    """
    Test registration failure when password and confirm password do not match.
    """
    page.goto(f"{live_server.url}/register/")

    # Scope the locator to the exact registration form to prevent interference
    register_form = page.locator("form").filter(has=page.locator("#id_password2"))

    page.locator("#id_username").fill("mismatchuser")
    page.locator("#id_email").fill("mismatch@isharerecipe.com")
    page.locator("#id_password1").fill("SecurePass123!")
    page.locator("#id_password2").fill("DifferentPass123!")

    # Submit the form and wait for the full page reload securely
    with page.expect_navigation():
        register_form.get_by_role("button", name="Create Account", exact=True).click()

    # Assert URL safely with regex to handle potential trailing slashes
    expect(page).to_have_url(re.compile(rf"^{re.escape(live_server.url)}/register/?$"))

    # Assert error message within the scoped form using regex to bypass typographic apostrophes
    password_mismatch_error = register_form.locator(".text-danger").filter(
        has_text=re.compile(r"didn.?t match", re.IGNORECASE)
    )

    # Strict assertions to prevent duplicate UI rendering (The Gold Standard)
    expect(password_mismatch_error).to_have_count(1)
    expect(password_mismatch_error).to_be_visible()

@qase.id(24)
def test_should_fail_login_when_username_is_invalid(page: Page, live_server):
    """
    Test login rejection when using an unregistered username.
    """
    page.goto(f"{live_server.url}/login/")

    # Scope the interaction to the exact login form
    login_form = page.locator("form").filter(has=page.locator("#id_username"))

    page.locator("#id_username").fill("nonexistentuser")
    page.locator("#id_password").fill("RandomPassword123!")

    # Submit the form and explicitly wait for the page navigation/reload
    with page.expect_navigation():
        login_form.get_by_role("button", name="Login", exact=True).click()

    # Assertion: Should remain on login page safely
    expect(page).to_have_url(re.compile(rf"^{re.escape(live_server.url)}/login/?$"))

    # Locate the error message dynamically within the broader card container
    # because login.html renders the alert box OUTSIDE the <form> tag
    auth_card = page.locator(".card").filter(has=page.locator("#id_username"))
    error_message = auth_card.get_by_text(re.compile(r"invalid username or password", re.IGNORECASE))

    # Strict assertions: Must appear exactly once
    expect(error_message).to_have_count(1)
    expect(error_message).to_be_visible()

@qase.id(25)
def test_should_fail_login_when_password_is_incorrect(page: Page, live_server, test_user):
    """
    Test login rejection when using a valid username but wrong password.
    """
    page.goto(f"{live_server.url}/login/")

    # Scope the interaction to the exact login form
    login_form = page.locator("form").filter(has=page.locator("#id_username"))

    page.locator("#id_username").fill(test_user.username)
    page.locator("#id_password").fill("WrongPassword999!")

    # Submit the form and explicitly wait for the page navigation/reload
    with page.expect_navigation():
        login_form.get_by_role("button", name="Login", exact=True).click()

    # Assertion: Should remain on login page safely
    expect(page).to_have_url(re.compile(rf"^{re.escape(live_server.url)}/login/?$"))

    # Locate the error message dynamically within the broader card container
    # because login.html renders the alert box OUTSIDE the <form> tag
    auth_card = page.locator(".card").filter(has=page.locator("#id_username"))
    error_message = auth_card.get_by_text(re.compile(r"invalid username or password", re.IGNORECASE))

    # Strict assertions: Must appear exactly once
    expect(error_message).to_have_count(1)
    expect(error_message).to_be_visible()

@qase.id(26)
def test_should_clear_authenticated_session_when_user_logs_out(page: Page, live_server, test_user):
    """
    Test successful logout flow via the navigation dropdown.
    """
    # Precondition: User is logged in
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Username").fill(test_user.username)
    page.get_by_label("Password", exact=True).fill("StrongTestPassword123!")

    with page.expect_navigation():
        page.get_by_role("button", name="Login", exact=True).click()

    expect(page.locator("#userDropdown")).to_have_count(1)

    # Action: Click User Avatar Dropdown -> Click Logout
    page.locator("#userDropdown").click()
    page.get_by_role("button", name="Logout").click()

    # Assertion: Should redirect to Login page safely
    expect(page).to_have_url(re.compile(rf"^{re.escape(live_server.url)}/login/?$"))

    # Assertion: Avatar dropdown should no longer be present
    expect(page.locator("#userDropdown")).not_to_be_visible()

@qase.id(27)
def test_should_recover_username_when_registered_email_is_submitted(page: Page, live_server, test_user):
    """
    Test the forgot username recovery flow.
    """
    page.goto(f"{live_server.url}/forgot-username/")

    # Action: Enter registered email
    page.get_by_label("Email Address").fill(test_user.email)

    with page.expect_navigation():
        page.get_by_role("button", name="Send Username").click()

    # Assertion: Success message should appear exactly once
    success_alert = page.locator(".alert").filter(has_text=re.compile(r"sent", re.IGNORECASE))

    # Strict assertions
    expect(success_alert).to_have_count(1)
    expect(success_alert).to_be_visible()

@qase.id(29)
def test_should_start_password_reset_flow_when_registered_account_requests_reset(page: Page, live_server, test_user):
    """
    Test the password reset initiation flow.
    """
    page.goto(f"{live_server.url}/password-reset/")

    # Action: Enter registered email
    page.locator("#id_email").fill(test_user.email)

    with page.expect_navigation():
        page.get_by_role("button", name="Send Reset Link").click()

    # Assertion: Success instructions are visible exactly once to ensure no duplicate rendering
    heading = page.get_by_role("heading", name="Check Your Inbox!")
    expect(heading).to_have_count(1)
    expect(heading).to_be_visible()

    instruction_text = page.locator("text=We've emailed you instructions for setting your password")
    expect(instruction_text).to_have_count(1)
    expect(instruction_text).to_be_visible()

@qase.id(30)
def test_should_preserve_authenticated_session_when_user_refreshes_the_page(page: Page, live_server, test_user):
    """
    Ensure the user remains authenticated after refreshing the browser.
    """
    # Precondition: Log in
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Username").fill(test_user.username)
    page.get_by_label("Password", exact=True).fill("StrongTestPassword123!")

    with page.expect_navigation():
        page.get_by_role("button", name="Login", exact=True).click()

    # Verify logged in state
    expect(page.locator("#userDropdown")).to_have_count(1)

    # Action: Reload the page
    page.reload()

    # Assertion: User should still be logged in
    expect(page.locator("#userDropdown")).to_have_count(1)
    expect(page.locator("#userDropdown")).to_be_visible()

@qase.id(32)
def test_should_treat_user_as_unauthenticated_when_session_cookie_is_removed(page: Page, live_server, test_user):
    """
    Verify application behavior when the session cookie is removed/expires.
    """
    # Precondition: Log in
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Username").fill(test_user.username)
    page.get_by_label("Password", exact=True).fill("StrongTestPassword123!")

    with page.expect_navigation():
        page.get_by_role("button", name="Login", exact=True).click()

    # Wait for successful login to complete
    expect(page.locator("#userDropdown")).to_be_visible()

    # Action: Simulate session expiration by clearing cookies
    page.context.clear_cookies()
    page.reload()

    # Assertion: User is treated as unauthenticated (Avatar disappears, Login button appears)
    expect(page.locator("#userDropdown")).not_to_be_visible()

    login_btn = page.get_by_role("link", name="Login", exact=True)
    expect(login_btn).to_have_count(1)
    expect(login_btn).to_be_visible()

@qase.id(34)
def test_should_reject_post_request_when_csrf_token_is_missing(page: Page, live_server, test_user):
    """
    Verify the application rejects POST requests with missing CSRF tokens.
    """
    page.goto(f"{live_server.url}/login/")

    # Action: Remove the hidden CSRF token from the DOM using JS evaluation
    page.evaluate('document.querySelector("input[name=\'csrfmiddlewaretoken\']").remove()')

    # Attempt to submit the form
    page.get_by_label("Username").fill(test_user.username)
    page.get_by_label("Password", exact=True).fill("StrongTestPassword123!")

    with page.expect_response(lambda response: response.status == 403) as response_info:
        page.get_by_role("button", name="Login", exact=True).click()

    # Assertion: Server should block the request with a 403 Forbidden status
    assert response_info.value.status == 403

@qase.id(36)
def test_should_set_httponly_flag_on_session_cookie_when_user_is_authenticated(page: Page, live_server, test_user):
    """
    Verify that the session cookie has HttpOnly flag set to prevent XSS hijacking.
    """
    # Precondition: Log in
    page.goto(f"{live_server.url}/login/")
    page.get_by_label("Username").fill(test_user.username)
    page.get_by_label("Password", exact=True).fill("StrongTestPassword123!")

    with page.expect_navigation():
        page.get_by_role("button", name="Login", exact=True).click()

    expect(page.locator("#userDropdown")).to_be_visible()

    # Action: Retrieve browser cookies
    cookies = page.context.cookies()
    session_cookie = next((c for c in cookies if c["name"] == "sessionid"), None)

    # Assertion: sessionid cookie must exist and must be HttpOnly
    assert session_cookie is not None, "Session cookie was not found"
    assert session_cookie["httpOnly"] is True, "Session cookie is vulnerable to XSS (HttpOnly is False)"

@qase.id(38)
def test_should_escape_malicious_script_content_when_recipe_is_rendered(page: Page, live_server, test_user):
    """
    Verify that malicious scripts in recipe titles and descriptions are safely escaped.
    """
    # Precondition: Inject a malicious payload directly into the database
    xss_payload = "<script>alert('XSS Exploit')</script>"
    recipe = Recipe.objects.create(
        title=xss_payload,
        description=xss_payload,
        ingredients="Test Ingredient",
        instructions="Test Instruction",
        author=test_user,
        country="US",
        tag="Dinner"
    )

    # Action: Navigate to the recipe detail page
    page.goto(f"{live_server.url}/recipe/{recipe.hashid}/")

    # Assertion 1: No dialog/alert should trigger (Playwright handles this implicitly,
    # but ensuring it renders as literal text exactly once proves it was escaped properly).
    title_element = page.locator("h1.text-primary", has_text=xss_payload)
    expect(title_element).to_have_count(1)
    expect(title_element).to_be_visible()

    # Assertion 2: Description also renders as safe literal text exactly once
    desc_element = page.locator("p.fst-italic", has_text=f'"{xss_payload}"')
    expect(desc_element).to_have_count(1)
    expect(desc_element).to_be_visible()

@qase.id(39)
def test_should_deny_recipe_edit_access_when_authenticated_user_is_not_the_owner(page: Page, live_server, test_user):
    """
    Verify that a user cannot edit another user's recipe by guessing the direct URL.
    """
    # Precondition 1: Create a recipe owned by 'test_user'
    target_recipe = Recipe.objects.create(
        title="Owner's Private Recipe",
        ingredients="Secret Ingredient",
        instructions="Secret Instruction",
        author=test_user,
        country="US",
        tag="Dinner"
    )

    # Precondition 2: Create and login as a different malicious user
    attacker = User.objects.create_user(username='attacker', password='MaliciousPassword123!')
    page.goto(f"{live_server.url}/login/")
    page.locator("#id_username").fill(attacker.username)
    page.locator("#id_password").fill("MaliciousPassword123!")

    with page.expect_navigation():
        page.get_by_role("button", name="Login", exact=True).click()

    expect(page.locator("#userDropdown")).to_be_visible()

    # Action: Attacker attempts to navigate to the edit URL of test_user's recipe
    edit_url = f"{live_server.url}/recipe/{target_recipe.hashid}/edit/"

    # Await the response to verify the server actively rejects the request
    response = page.goto(edit_url)

    # Assertion 1: Server should return 403 Forbidden (or redirect via 302, but typically 403)
    assert response.status in [403, 302], f"Expected 403 or 302, but got {response.status}"

    # Assertion 2: The actual recipe edit form must NOT be rendered in the DOM
    expect(page.locator("#recipeForm")).not_to_be_visible()
