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
    Seeds the database with specific recipes to fulfill filter and interaction test requirements.
    Uses ISO-3166 alpha-2 country codes to strictly respect the max_length=2 model constraint.
    """
    from recipes.models import Recipe

    # Recipe 1: Designed to show up in Trending & Saved (Liked and Saved by test_user)
    r1 = Recipe.objects.create(
        title="Vietnamese Cassava Coconut Cake",
        description="A traditional sweet treat.",
        ingredients="cassava, coconut, sugar, milk",
        instructions="Mix and bake.",
        country="VN",
        tag="Dessert",
        author=test_user
    )
    r1.likes.add(test_user)
    r1.saved_by.add(test_user)

    # Recipe 2: Designed for Latest and partial searches
    user2 = User.objects.create_user(username='chef_japan', password='pwd')
    r2 = Recipe.objects.create(
        title="Quick Salmon Sushi",
        description="Easy homemade sushi.",
        ingredients="salmon, rice, seaweed, vinegar",
        instructions="Roll and slice.",
        country="JP",
        tag="Lunch",
        author=user2
    )
    # Add a like to ensure it appears in the Trending section for interaction tests
    r2.likes.add(user2)

    return [r1, r2]


@pytest.fixture
def auth_page(page: Page, live_server, test_user) -> Page:
    """
    Logs in the test_user and yields an authenticated Playwright page.
    Explicitly targets the submit button that is NOT the navbar search button.
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

@qase.id(93)
def test_should_display_home_page_layout_and_navigation_elements_when_authenticated(auth_page: Page, seeded_recipes):
    """Covers TC1, TC2, TC3, TC4, TC5, TC6, TC7, TC8, TC34, TC35"""
    expect(auth_page.locator("h2:has-text('Trending Recipes')")).to_be_visible()
    expect(auth_page.locator("h2:has-text('Latest Recipes')")).to_be_visible()
    expect(auth_page.locator("h2:has-text('Saved Recipes')")).to_be_visible()

    expect(auth_page.locator("#viewAllLatestBtn")).to_be_visible()
    expect(auth_page.locator("#viewAllSavedBtn")).to_be_visible()

    expect(auth_page.locator("input[name='q']")).to_be_visible()
    expect(auth_page.locator("input[name='q']")).to_be_enabled()

    expect(auth_page.locator("a[title='Notifications']")).to_be_visible()
    expect(auth_page.locator("a[title='Saved Recipes']")).to_be_visible()

    expect(auth_page.locator("a:has-text('+ Add Recipe')")).to_be_visible()


@qase.id(94)
def test_should_display_all_filter_and_search_controls_on_home_page_when_authenticated(auth_page: Page):
    """Covers TC9, TC10, TC11, TC12, TC13, TC14, TC15"""
    expect(auth_page.locator("#ingredientSearchInput")).to_be_visible()
    expect(auth_page.locator("#ingredientSearchInput")).to_be_enabled()
    expect(auth_page.locator("#ingredientSearchBtn")).to_be_visible()
    expect(auth_page.locator("#ingredientSearchBtn")).to_be_enabled()

    expect(auth_page.locator("#countryFilterBtn")).to_be_visible()
    expect(auth_page.locator("#countryFilterBtn")).to_be_enabled()

    expect(auth_page.locator("#tagFilterBtn")).to_be_visible()
    expect(auth_page.locator("#tagFilterBtn")).to_be_enabled()

    expect(auth_page.locator("#mostLikedBtn")).to_be_visible()
    expect(auth_page.locator("#mostLikedBtn")).to_be_enabled()

    expect(auth_page.locator("#authorFilterBtn")).to_be_visible()
    expect(auth_page.locator("#authorFilterBtn")).to_be_enabled()

    expect(auth_page.locator("#refreshFilterBtn")).to_be_visible()
    expect(auth_page.locator("#refreshFilterBtn")).to_be_enabled()


@qase.id(95)
def test_should_navigate_to_add_recipe_page_when_accessed_via_direct_url(auth_page: Page, live_server):
    """Covers TC22"""
    auth_page.goto(f"{live_server.url}/recipe/add/")
    expect(auth_page).to_have_url(re.compile(r".*/recipe/add/"))


@qase.id(96)
def test_should_filter_recipes_successfully_when_searching_by_exact_partial_or_multiple_ingredients(auth_page: Page,
                                                                                                    seeded_recipes):
    """Covers TC36, TC37, TC38"""
    auth_page.fill("#ingredientSearchInput", "cassava, sugar")

    with auth_page.expect_response(lambda response: "/api/filter-home/" in response.url and response.status == 200):
        auth_page.click("#ingredientSearchBtn")

    expect(auth_page.locator("#recent-wrapper .scrolling-card")).to_have_count(1)
    expect(auth_page.locator("#recent-wrapper .scrolling-card").first).to_contain_text(
        "Vietnamese Cassava Coconut Cake")


@qase.id(97)
def test_should_filter_recipes_successfully_when_applying_dropdown_and_toggle_filters(auth_page: Page, seeded_recipes):
    """Covers TC39, TC40, TC41, TC42, TC43"""
    auth_page.click("#countryFilterBtn")
    auth_page.fill("#countrySearchInput", "Japan")  # Fills input to trigger UI render

    with auth_page.expect_response(lambda response: "/api/filter-home/" in response.url and response.status == 200):
        auth_page.locator("#countryDropdownList button", has_text="Japan").click()

    expect(auth_page.locator("#recent-wrapper .scrolling-card")).to_have_count(1)
    expect(auth_page.locator("#recent-wrapper .scrolling-card").first).to_contain_text("Quick Salmon Sushi")

    auth_page.click("#tagFilterBtn")
    with auth_page.expect_response(lambda response: "/api/filter-home/" in response.url and response.status == 200):
        auth_page.locator(".tag-item[data-val='Lunch']").click()

    expect(auth_page.locator("#recent-wrapper .scrolling-card")).to_have_count(1)


@qase.id(98)
def test_should_clear_dropdown_filters_and_restore_default_display_when_refresh_icon_is_clicked(auth_page: Page,
                                                                                                seeded_recipes):
    """Covers TC44, TC45, TC46, TC47"""
    auth_page.click("#countryFilterBtn")
    auth_page.fill("#countrySearchInput", "Japan")
    with auth_page.expect_response(lambda response: "/api/filter-home/" in response.url and response.status == 200):
        auth_page.locator("#countryDropdownList button", has_text="Japan").click()

    expect(auth_page.locator("#recent-wrapper .scrolling-card")).to_have_count(1)

    with auth_page.expect_response(lambda response: "/api/filter-home/" in response.url and response.status == 200):
        auth_page.click("#refreshFilterBtn")

    expect(auth_page.locator("#recent-wrapper .scrolling-card")).to_have_count(2)


@qase.id(99)
def test_should_retain_ingredient_search_value_but_clear_dropdown_filters_when_refresh_icon_is_clicked(auth_page: Page,
                                                                                                       seeded_recipes):
    """Covers TC48, TC49"""
    auth_page.fill("#ingredientSearchInput", "salmon")
    with auth_page.expect_response(lambda response: "/api/filter-home/" in response.url and response.status == 200):
        auth_page.click("#ingredientSearchBtn")

    auth_page.click("#countryFilterBtn")
    auth_page.fill("#countrySearchInput", "Japan")
    with auth_page.expect_response(lambda response: "/api/filter-home/" in response.url and response.status == 200):
        auth_page.locator("#countryDropdownList button", has_text="Japan").click()

    with auth_page.expect_response(lambda response: "/api/filter-home/" in response.url and response.status == 200):
        auth_page.click("#refreshFilterBtn")

    expect(auth_page.locator("#ingredientSearchInput")).to_have_value("salmon")
    expect(auth_page.locator("#recent-wrapper .scrolling-card")).to_have_count(1)
    expect(auth_page.locator("#countryFilterBtn")).to_have_text("Country")


@qase.id(100)
def test_should_display_empty_state_when_filters_yield_no_matching_recipes(auth_page: Page, seeded_recipes):
    """Covers TC50, TC51, TC52, TC53, TC54"""
    auth_page.fill("#ingredientSearchInput", "unicorn meat")

    with auth_page.expect_response(lambda response: "/api/filter-home/" in response.url and response.status == 200):
        auth_page.click("#ingredientSearchBtn")

    # Safe check for empty state: count DOM nodes instead of asserting exact empty string text
    expect(auth_page.locator("#recent-wrapper .scrolling-card")).to_have_count(0)
    expect(auth_page.locator("#trending-wrapper .scrolling-card")).to_have_count(0)

    auth_page.fill("#ingredientSearchInput", "")
    with auth_page.expect_response(lambda response: "/api/filter-home/" in response.url and response.status == 200):
        auth_page.click("#ingredientSearchBtn")

    expect(auth_page.locator("#recent-wrapper .scrolling-card")).to_have_count(2)
