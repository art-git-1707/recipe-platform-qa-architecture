import pytest
import re
from playwright.sync_api import Page, expect
from django.contrib.auth.models import User
from qase.pytest import qase

# Apply the database mark to all tests in this file so they can interact with the DB
pytestmark = pytest.mark.django_db


# ==========================================
# FIXTURE OVERRIDES & DATA SEEDING
# ==========================================
@pytest.fixture
def seeded_recipes(transactional_db, test_user):
    """
    Seeds the database with strictly controlled recipes.
    """
    from recipes.models import Recipe
    user2 = User.objects.create_user(username='chef_japan', password='pwd')

    # Recipe 1: Owned by test_user. Designed for Edit/Delete permission testing.
    r1 = Recipe.objects.create(
        title="Vietnamese Cassava Coconut Cake",
        description="A traditional sweet treat.",
        ingredients="cassava\ncoconut\nsugar\nmilk",
        instructions="Mix ingredients.\nBake for 30 mins.",
        country="VN",
        tag="Dessert",
        author=test_user
    )
    r1.likes.add(test_user, user2)
    r1.saved_by.add(test_user)

    # Recipe 2: Owned by user2. Designed for unauthorized Edit/Delete testing.
    r2 = Recipe.objects.create(
        title="Quick Salmon Sushi",
        description="Easy homemade sushi.",
        ingredients="salmon\nrice\nseaweed",
        instructions="Roll everything.\nSlice and serve.",
        country="JP",
        tag="Lunch",
        author=user2
    )
    r2.likes.add(user2)

    return [r1, r2]


@pytest.fixture
def auth_page(page: Page, live_server, test_user, seeded_recipes) -> Page:
    """
    Logs in the test_user and yields an authenticated Playwright page.
    CRITICAL FIX: By injecting 'seeded_recipes' here, we enforce Pytest to seed the DB
    BEFORE the browser navigates to the Home page. This prevents empty DOM timeouts.
    """
    page.goto(f"{live_server.url}/login/")
    page.fill("input[name='username']", test_user.username)
    page.fill("input[name='password']", "StrongTestPassword123!")

    # Safe Locator: Exclude global search button
    page.locator("button[type='submit']:not(#search-addon)").click()

    expect(page).to_have_url(f"{live_server.url}/")
    return page


# ==========================================
# TEST AUTOMATION SUITE
# ==========================================

@qase.id(101)
def test_should_navigate_to_recipe_details_from_home_page_sections(auth_page: Page, seeded_recipes):
    """Covers TC1, TC2, TC4: Navigation from Trending, Latest, and View All Latest"""

    # TC1: Navigate via Trending Recipes section
    trending_card = auth_page.locator("#trending-wrapper .scrolling-card").first
    trending_card.click()
    expect(auth_page).to_have_url(re.compile(r".*/recipe/[a-zA-Z0-9]+/.*"))
    auth_page.goto(auth_page.url.split("/recipe/")[0] + "/")  # Go back home

    # TC2: Navigate via Latest Recipes section
    recent_card = auth_page.locator("#recent-wrapper .scrolling-card").first
    recent_card.click()
    expect(auth_page).to_have_url(re.compile(r".*/recipe/[a-zA-Z0-9]+/.*"))
    auth_page.goto(auth_page.url.split("/recipe/")[0] + "/")  # Go back home

    # TC4: Navigate via View All Latest
    auth_page.click("#viewAllLatestBtn")
    expect(auth_page).to_have_url(re.compile(r".*/latest/.*"))
    latest_page_card = auth_page.locator("#recipe-grid .recipe-card-item .card").first
    latest_page_card.click()
    expect(auth_page).to_have_url(re.compile(r".*/recipe/[a-zA-Z0-9]+/.*"))


@qase.id(102)
def test_should_navigate_to_recipe_details_via_global_search_by_exact_and_partial_name(auth_page: Page, seeded_recipes):
    """Covers TC5, TC6: Global search navigation"""

    # TC5: Exact search
    auth_page.fill("input[name='q']", "Quick Salmon Sushi")
    auth_page.press("input[name='q']", "Enter")
    expect(auth_page.locator("#recipe-grid .recipe-card-item .card")).to_have_count(1)
    auth_page.locator("#recipe-grid .recipe-card-item .card").first.click()
    expect(auth_page.locator("h1.display-5")).to_have_text("Quick Salmon Sushi")

    # TC6: Partial search
    auth_page.fill("input[name='q']", "Cassava")
    auth_page.press("input[name='q']", "Enter")
    expect(auth_page.locator("#recipe-grid .recipe-card-item .card")).to_have_count(1)
    auth_page.locator("#recipe-grid .recipe-card-item .card").first.click()
    expect(auth_page.locator("h1.display-5")).to_have_text("Vietnamese Cassava Coconut Cake")


@qase.id(103)
def test_should_display_recipe_details_accurately_when_accessed_directly(auth_page: Page, live_server, seeded_recipes):
    """Covers TC3, TC13, TC14, TC15, TC16: Direct access and data matching"""
    own_recipe = seeded_recipes[0]
    detail_url = f"{live_server.url}/recipe/{own_recipe.hashid}/"

    # Get counts from home page first to match later (Safely available since DB is seeded before auth_page)
    home_like_count = auth_page.locator("#trending-wrapper .scrolling-card").first.locator(
        "span.fw-bold").first.inner_text()

    # TC3: Direct link access
    auth_page.goto(detail_url)
    expect(auth_page).to_have_url(detail_url)
    expect(auth_page.locator("h1.display-5")).to_have_text(own_recipe.title)

    # TC13: Ingredients section visible and populated
    expect(auth_page.locator("#ingredients-ui-list li")).to_have_count(4)  # 4 ingredients

    # TC14: Instructions section visible and populated
    expect(auth_page.locator("#instructions-ui-list li")).to_have_count(2)  # 2 steps

    # TC15 & TC16: Total likes and saves match UI
    detail_like_count = auth_page.locator(f"strong.like-count-{own_recipe.hashid}")
    expect(detail_like_count).to_have_text(home_like_count)

    detail_save_count = auth_page.locator(f"strong.save-count-{own_recipe.hashid}")
    expect(detail_save_count).to_have_text("1")  # Seeded as 1 for test_user


@qase.id(104)
def test_should_update_like_and_save_counts_on_recipe_details_page_when_interacted(auth_page: Page, live_server,
                                                                                   seeded_recipes):
    """Covers TC7, TC8: Like and Save interaction on details page"""
    other_recipe = seeded_recipes[1]  # Using recipe 2 (unliked, unsaved by test_user)
    auth_page.goto(f"{live_server.url}/recipe/{other_recipe.hashid}/")

    like_count_locator = f"strong.like-count-{other_recipe.hashid}"
    save_count_locator = f"strong.save-count-{other_recipe.hashid}"

    # Check initial
    expect(auth_page.locator(like_count_locator)).to_have_text("1")
    expect(auth_page.locator(save_count_locator)).to_have_text("0")

    # TC7: Like increase (Wait for API -> Reload page to bypass WebSocket limits -> Assert DB update)
    with auth_page.expect_response(lambda response: "/like/" in response.url and response.status == 200):
        auth_page.locator("button[title='Like']").click()
    auth_page.reload()
    expect(auth_page.locator(like_count_locator)).to_have_text("2")

    # TC8: Save increase
    with auth_page.expect_response(lambda response: "/save/" in response.url and response.status == 200):
        auth_page.locator("button[title='Save']").click()
    auth_page.reload()
    expect(auth_page.locator(save_count_locator)).to_have_text("1")


@qase.id(105)
def test_should_copy_recipe_url_to_clipboard_when_share_button_is_clicked(auth_page: Page, live_server, seeded_recipes):
    """Covers TC9: Share button clipboard interaction"""
    own_recipe = seeded_recipes[0]
    detail_url = f"{live_server.url}/recipe/{own_recipe.hashid}/"

    # CRITICAL: Grant clipboard permissions for headless execution
    auth_page.context.grant_permissions(['clipboard-read', 'clipboard-write'])

    auth_page.goto(detail_url)

    share_btn = auth_page.locator("button[title='Copy Link to Share']")
    share_text = share_btn.locator(".share-text")

    expect(share_text).to_have_text("Share")
    share_btn.click()

    # Verify UI state change
    expect(share_text).to_have_text("Copied!")

    # Verify clipboard content matches current URL
    clipboard_content = auth_page.evaluate("navigator.clipboard.readText()")
    assert clipboard_content == detail_url, "Clipboard content does not match the expected Recipe URL"


@qase.id(106)
def test_should_restrict_edit_and_delete_actions_to_recipe_owner(auth_page: Page, live_server, seeded_recipes):
    """Covers TC10, TC11, TC12: Security boundary for non-authors"""
    own_recipe = seeded_recipes[0]
    other_recipe = seeded_recipes[1]

    # TC10: '...' menu visible for own recipe
    auth_page.goto(f"{live_server.url}/recipe/{own_recipe.hashid}/")
    expect(auth_page.locator("#recipeActionMenu")).to_be_visible()

    # TC10: '...' menu NOT visible for others recipe
    auth_page.goto(f"{live_server.url}/recipe/{other_recipe.hashid}/")
    expect(auth_page.locator("#recipeActionMenu")).not_to_be_visible()

    # TC11 & TC12: Cannot access edit page via direct link for others recipe
    auth_page.goto(f"{live_server.url}/recipe/{other_recipe.hashid}/edit/")
    # Assert we are denied access (recipe form should not render)
    expect(auth_page.locator("#recipeForm")).not_to_be_visible()


@qase.id(107)
def test_should_allow_owner_to_edit_recipe_successfully(auth_page: Page, live_server, seeded_recipes):
    """Covers TC17: Edit own recipe flow"""
    own_recipe = seeded_recipes[0]
    auth_page.goto(f"{live_server.url}/recipe/{own_recipe.hashid}/")

    # Open action menu and click edit
    auth_page.locator("#recipeActionMenu").click()
    auth_page.locator("a:has-text('Edit Recipe')").click()

    expect(auth_page).to_have_url(f"{live_server.url}/recipe/{own_recipe.hashid}/edit/")

    # Modify data
    auth_page.fill("input[name='title']", "Updated Cassava Cake")
    auth_page.locator("#recipeForm button[type='submit']").click()

    # Assert successful redirect and update
    expect(auth_page).to_have_url(f"{live_server.url}/recipe/{own_recipe.hashid}/")
    expect(auth_page.locator("h1.display-5")).to_have_text("Updated Cassava Cake")


@qase.id(108)
def test_should_allow_owner_to_delete_recipe_successfully(auth_page: Page, live_server, seeded_recipes):
    """Covers TC18: Delete own recipe flow"""
    own_recipe = seeded_recipes[0]
    auth_page.goto(f"{live_server.url}/recipe/{own_recipe.hashid}/")

    # Open action menu and click delete
    auth_page.locator("#recipeActionMenu").click()
    auth_page.locator("button[data-bs-target='#deleteModal']").click()

    # Wait for modal animation to complete safely
    delete_modal = auth_page.locator("#deleteModal")
    expect(delete_modal).to_be_visible()

    # Confirm deletion
    delete_modal.locator("button[type='submit']:has-text('Yes, Delete')").click()

    # Assert successful redirect to home
    expect(auth_page).to_have_url(f"{live_server.url}/")

    # Assert recipe is no longer visible on home page
    expect(auth_page.locator("#trending-wrapper .scrolling-card", has_text=own_recipe.title)).not_to_be_visible()
