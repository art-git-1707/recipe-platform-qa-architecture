import pytest
from PIL import Image
from playwright.sync_api import Page, expect
from qase.pytest import qase
from recipes.models import Recipe


# Apply the database mark to all tests in this file so they can interact with the DB
pytestmark = pytest.mark.django_db

# ==========================================
# FIXTURES (SETUP DATA)
# ==========================================
@pytest.fixture
def dummy_image_path(tmp_path):
    """
    Dynamically generates a temporary JPG image file for upload testing.
    This also implicitly tests your models.py WebP compression logic!
    """
    image = Image.new('RGB', (1200, 800), color='coral')
    img_path = tmp_path / "test_upload.jpg"
    image.save(img_path)
    return str(img_path)

@pytest.fixture
def sample_recipe(test_user):
    """
    Creates a sample recipe directly in the database to test
    interaction features (Like/Save) without having to UI-create it first.
    """
    return Recipe.objects.create(
        title="Playwright Interactive Recipe",
        description="A recipe forged in the fires of CI/CD.",
        ingredients="1 cup magic\n2 tbsp code",
        instructions="Mix asynchronously and await.",
        prep_time=5,
        cook_time=10,
        servings=2,
        country="VN",
        tag="Lunch",
        author=test_user
    )

# ==========================================
# REGRESSION - TEST CASE
# ==========================================
@qase.id(1)
def test_user_login_success(page: Page, live_server, test_user):
    """
    Simulates a user navigating to the login page, entering valid credentials,
    and verifying successful redirection to the home page.
    """
    page.goto(f"{live_server.url}/login/")

    page.fill('input[name="username"]', 'testautomation')
    page.fill('input[name="password"]', 'StrongTestPassword123!')

    # Specific locator for the POST form submit button
    page.locator('form[method="post"] button[type="submit"]').click()

    # Check if the URL successfully changed to the Home page
    expect(page).to_have_url(f"{live_server.url}/")

    # FIX: Since the username is hidden inside a dropdown, we first need to click the avatar to open the dropdown
    page.locator('#userDropdown').click()

    # Now we can expect the username to be visible
    expect(page.locator(f"text={test_user.username}")).to_be_visible()

@qase.id(2)
def test_invalidUser_login_failure(page: Page, live_server):
    """
    Simulates a user entering incorrect credentials and verifies that
    the system rejects the login attempt.
    """
    page.goto(f"{live_server.url}/login/")

    page.fill('input[name="username"]', 'wronguser')
    page.fill('input[name="password"]', 'StrongTestPassword123!')

    page.locator('form[method="post"] button[type="submit"]').click()

    expect(page).to_have_url(f"{live_server.url}/login/")

    # FIX: Target the Django form error alert box specifically
    error_alert = page.locator('.alert-error')
    expect(error_alert).to_be_visible()

    # Or specifically check the text content if you prefer:
    expect(error_alert).to_contain_text("Invalid username or password.")

@qase.id(3)
def test_invalidPassword_login_failure(page: Page, live_server):
    """
    Simulates a user entering incorrect credentials and verifies that
    the system rejects the login attempt.
    """
    page.goto(f"{live_server.url}/login/")

    page.fill('input[name="username"]', 'testautomation')
    page.fill('input[name="password"]', 'wrongpassword')

    page.locator('form[method="post"] button[type="submit"]').click()

    expect(page).to_have_url(f"{live_server.url}/login/")

    # FIX: Target the Django form error alert box specifically
    error_alert = page.locator('.alert-error')
    expect(error_alert).to_be_visible()

    # Or specifically check the text content if you prefer:
    expect(error_alert).to_contain_text("Invalid username or password.")

@qase.id(4)
def test_user_registration_success(page: Page, live_server):
    """
    Simulates a new user filling out the registration form and verifying
    they are automatically logged in and redirected.
    """
    page.goto(f"{live_server.url}/register/")

    page.fill('input[name="username"]', 'newplaywrightuser')
    page.fill('input[name="email"]', 'new_user@isharerecipe.com')

    passwords = page.locator('input[type="password"]')
    passwords.nth(0).fill('SecureNewPass123!')
    passwords.nth(1).fill('SecureNewPass123!')

    page.locator('form[method="post"] button[type="submit"]').click()

    expect(page).to_have_url(f"{live_server.url}/")

    # FIX: Click the avatar to open the dropdown before asserting visibility
    page.locator('#userDropdown').click()
    expect(page.locator("text=newplaywrightuser")).to_be_visible()

@qase.id(6)
def test_create_new_recipe(page: Page, live_server, test_user, dummy_image_path):
    """
    Tests the End-to-End flow of logging in, filling out the recipe form,
    uploading an image, and verifying the new recipe is displayed correctly.
    """
    page.goto(f"{live_server.url}/login/")
    page.fill('input[name="username"]', 'testautomation')
    page.fill('input[name="password"]', 'StrongTestPassword123!')
    page.locator('form[method="post"] button[type="submit"]').click()

    expect(page).to_have_url(f"{live_server.url}/")

    page.goto(f"{live_server.url}/recipe/add/")

    page.fill('input[name="title"]', 'Automated Masterpiece')
    page.fill('textarea[name="description"]', 'A delicious automated test recipe.')
    page.fill('textarea[name="ingredients"]', '100g Python\n50g Playwright')
    page.fill('textarea[name="instructions"]', '1. Write test.\n2. Watch it pass.')
    page.fill('input[name="prep_time"]', '10')
    page.fill('input[name="cook_time"]', '20')
    page.fill('input[name="servings"]', '4')

    page.select_option('select[name="country"]', 'VN', force=True)
    page.select_option('select[name="tag"]', 'Dinner', force=True)

    page.set_input_files('input[type="file"]', dummy_image_path)

    page.get_by_role("button", name="Save Recipe").click()

    expect(page).not_to_have_url(f"{live_server.url}/recipe/add/")

    expect(page.locator("h1", has_text="Automated Masterpiece")).to_be_visible()

@qase.id(7)
def test_user_liked_saved_recipe(page: Page, live_server, test_user, sample_recipe):
    """
    Tests the interaction features: Liking and Saving a recipe.
    """
    page.goto(f"{live_server.url}/login/")
    page.fill('input[name="username"]', 'testautomation')
    page.fill('input[name="password"]', 'StrongTestPassword123!')
    page.locator('form[method="post"] button[type="submit"]').click()

    page.goto(f"{live_server.url}/recipe/{sample_recipe.hashid}/")

    like_button = page.locator('button').filter(has=page.locator('i[class*="bi-hand-thumbs-up"]'))
    like_count_element = page.locator(f'.like-count-{sample_recipe.hashid}')

    with page.expect_response(lambda response: "/like/" in response.url and response.status == 200):
        like_button.click()

    page.reload()

    # Check in strong element has class like-count = 1
    expect(like_count_element).to_contain_text('1')

    # Test Save Functionality
    save_button = page.locator('button').filter(has=page.locator('i[class*="bi-heart"]'))
    with page.expect_response(lambda response: "/save/" in response.url and response.status == 200):
        save_button.click()

    page.goto(f"{live_server.url}/saved/")
    expect(page.locator(f'text={sample_recipe.title}')).to_be_visible()
