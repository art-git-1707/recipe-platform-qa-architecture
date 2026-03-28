import pytest
from playwright.sync_api import Page, expect
from django.contrib.auth.models import User
from recipes.models import Recipe
import re
from qase.pytest import qase

# ==========================================
# TEST FIXTURES FOR DETERMINISTIC STATE
# ==========================================
@pytest.fixture
def seeded_recipe(db, test_user):
    """
    Ensures at least one recipe exists in the database so that
    the Trending and Latest wrappers render recipe cards instead of empty states.
    """
    recipe = Recipe.objects.create(
        title="Automated Test Recipe",
        description="A robust recipe for UI automation.",
        ingredients="1 cup stability\n2 tbsp determinism",
        instructions="Mix well without implicit waits.",
        prep_time=10,
        cook_time=20,
        author=test_user,
        country="VN",
        tag="Lunch"
    )
    return recipe


# ==========================================
# TEST FIXTURES FOR FILTERING TESTS
# ==========================================

@pytest.fixture
def seeded_recipes_for_filtering(db, test_user):
    """
    Creates multiple recipes with different attributes to test filtering functionality.
    """
    recipe1 = Recipe.objects.create(
        title="Cassava Cake",
        description="A traditional dessert.",
        ingredients="cassava, coconut milk, sugar",
        instructions="Mix and bake.",
        prep_time=15,
        cook_time=45,
        author=test_user,
        country="VN",
        tag="Dessert"
    )

    recipe2 = Recipe.objects.create(
        title="American Burger",
        description="Classic beef burger.",
        ingredients="beef patty, bun, cheese, lettuce",
        instructions="Grill patty and assemble.",
        prep_time=10,
        cook_time=10,
        author=test_user,
        country="US",
        tag="Lunch"
    )

    # Simulate some likes for the "Most Liked" filter
    user2 = User.objects.create_user(username='liker1', password='pw')
    recipe2.likes.add(user2)

    return [recipe1, recipe2]

# ==========================================
# TEST SUITE: HOME PAGE & GUEST INTERACTIONS
# ==========================================

@qase.id(40)
def test_should_display_home_page_successfully_for_unauthenticated_user(page: Page, live_server):
    page.goto(live_server.url)

    # Assert main hero header is visible
    hero_header = page.locator("h1.display-4.fw-bold.text-primary")
    expect(hero_header).to_be_visible()
    expect(hero_header).to_have_text("Discover Delicious Recipes")


@qase.id(41)
def test_should_display_trending_recipes_section_on_home_page(page: Page, live_server):
    page.goto(live_server.url)

    trending_heading = page.get_by_role("heading", name="Trending Recipes", exact=True)
    trending_wrapper = page.locator("#trending-wrapper")

    expect(trending_heading).to_be_visible()
    expect(trending_wrapper).to_be_visible()


@qase.id(42)
def test_should_display_latest_recipes_section_on_home_page(page: Page, live_server):
    page.goto(live_server.url)

    latest_heading = page.get_by_role("heading", name="Latest Recipes", exact=True)
    recent_wrapper = page.locator("#recent-wrapper")

    expect(latest_heading).to_be_visible()
    expect(recent_wrapper).to_be_visible()


@qase.id(43)
def test_should_enable_global_search_bar_for_unauthenticated_user(page: Page, live_server):
    page.goto(live_server.url)

    search_input = page.locator('input[name="q"]')
    expect(search_input).to_be_visible()
    expect(search_input).to_be_enabled()
    expect(search_input).to_have_attribute("placeholder", "Search for recipes...")


@qase.id(44)
def test_should_enable_login_button_in_navbar_for_guest(page: Page, live_server):
    page.goto(live_server.url)

    login_button = page.get_by_role("link", name="Login", exact=True)
    expect(login_button).to_be_visible()
    expect(login_button).to_be_enabled()
    expect(login_button).to_have_attribute("href", "/login/")


@qase.id(45)
def test_should_enable_sign_up_button_in_navbar_for_guest(page: Page, live_server):
    page.goto(live_server.url)

    signup_button = page.get_by_role("link", name="Sign Up", exact=True)
    expect(signup_button).to_be_visible()
    expect(signup_button).to_be_enabled()
    expect(signup_button).to_have_attribute("href", "/register/")


@qase.id(46)
def test_should_enable_ingredient_search_input_on_home_page(page: Page, live_server):
    page.goto(live_server.url)

    ingredient_input = page.locator("#ingredientSearchInput")
    expect(ingredient_input).to_be_visible()
    expect(ingredient_input).to_be_enabled()


@qase.id(47)
def test_should_enable_ingredient_search_button_on_home_page(page: Page, live_server):
    page.goto(live_server.url)

    ingredient_search_btn = page.locator("#ingredientSearchBtn")
    expect(ingredient_search_btn).to_be_visible()
    expect(ingredient_search_btn).to_be_enabled()


@qase.id(48)
def test_should_enable_country_filter_dropdown_on_home_page(page: Page, live_server):
    page.goto(live_server.url)

    country_btn = page.locator("#countryFilterBtn")
    expect(country_btn).to_be_visible()
    expect(country_btn).to_be_enabled()


@qase.id(49)
def test_should_enable_category_tag_filter_dropdown_on_home_page(page: Page, live_server):
    page.goto(live_server.url)

    tag_btn = page.locator("#tagFilterBtn")
    expect(tag_btn).to_be_visible()
    expect(tag_btn).to_be_enabled()


@qase.id(50)
def test_should_enable_most_liked_filter_toggle_on_home_page(page: Page, live_server):
    page.goto(live_server.url)

    most_liked_btn = page.locator("#mostLikedBtn")
    expect(most_liked_btn).to_be_visible()
    expect(most_liked_btn).to_be_enabled()


@qase.id(51)
def test_should_enable_posted_by_author_filter_dropdown_on_home_page(page: Page, live_server):
    page.goto(live_server.url)

    author_btn = page.locator("#authorFilterBtn")
    expect(author_btn).to_be_visible()
    expect(author_btn).to_be_enabled()


@qase.id(52)
def test_should_enable_refresh_filters_button_on_home_page(page: Page, live_server):
    page.goto(live_server.url)

    refresh_btn = page.locator("#refreshFilterBtn")
    expect(refresh_btn).to_be_visible()
    expect(refresh_btn).to_be_enabled()


@qase.id(53)
def test_should_display_like_icon_in_trending_section_when_recipe_exists(page: Page, live_server, seeded_recipe):
    page.goto(live_server.url)

    trending_wrapper = page.locator("#trending-wrapper")
    like_icon = trending_wrapper.locator("span[title='Like']").first

    expect(like_icon).to_be_visible()


@qase.id(54)
def test_should_display_save_icon_in_trending_section_when_recipe_exists(page: Page, live_server, seeded_recipe):
    page.goto(live_server.url)

    trending_wrapper = page.locator("#trending-wrapper")
    save_icon = trending_wrapper.locator("span[title='Save']").first

    expect(save_icon).to_be_visible()


@qase.id(55)
def test_should_display_like_icon_in_latest_section_when_recipe_exists(page: Page, live_server, seeded_recipe):
    page.goto(live_server.url)

    recent_wrapper = page.locator("#recent-wrapper")
    like_icon = recent_wrapper.locator("span[title='Like']").first

    expect(like_icon).to_be_visible()


@qase.id(56)
def test_should_display_save_icon_in_latest_section_when_recipe_exists(page: Page, live_server, seeded_recipe):
    page.goto(live_server.url)

    recent_wrapper = page.locator("#recent-wrapper")
    save_icon = recent_wrapper.locator("span[title='Save']").first

    expect(save_icon).to_be_visible()


@qase.id(57)
def test_should_hide_add_recipe_button_from_unauthenticated_user(page: Page, live_server):
    page.goto(live_server.url)

    add_recipe_btn = page.get_by_role("link", name="+ Add Recipe")
    expect(add_recipe_btn).not_to_be_attached()


@qase.id(58)
def test_should_redirect_to_login_when_unauthenticated_user_accesses_add_recipe_url(page: Page, live_server):
    page.goto(f"{live_server.url}/recipe/add/")

    # Wait for URL to contain login redirection
    expect(page).to_have_url(f"{live_server.url}/login/?next=/recipe/add/")


@qase.id(59)
def test_should_show_auth_modal_when_guest_clicks_like_button_in_trending_section(page: Page, live_server,
                                                                                  seeded_recipe):
    page.goto(live_server.url)

    trending_wrapper = page.locator("#trending-wrapper")
    like_icon = trending_wrapper.locator("span[title='Like']").first
    like_icon.click()

    auth_modal = page.locator("#authModal")
    modal_title = page.locator("#authModalLabel")

    expect(auth_modal).to_be_visible()
    expect(modal_title).to_have_text("Join our community!")


@qase.id(60)
def test_should_show_auth_modal_when_guest_clicks_save_button_in_trending_section(page: Page, live_server,
                                                                                  seeded_recipe):
    page.goto(live_server.url)

    trending_wrapper = page.locator("#trending-wrapper")
    save_icon = trending_wrapper.locator("span[title='Save']").first
    save_icon.click()

    auth_modal = page.locator("#authModal")
    modal_title = page.locator("#authModalLabel")

    expect(auth_modal).to_be_visible()
    expect(modal_title).to_have_text("Join our community!")


@qase.id(61)
def test_should_show_auth_modal_when_guest_clicks_like_button_in_latest_section(page: Page, live_server, seeded_recipe):
    page.goto(live_server.url)

    recent_wrapper = page.locator("#recent-wrapper")
    like_icon = recent_wrapper.locator("span[title='Like']").first
    like_icon.click()

    auth_modal = page.locator("#authModal")
    modal_title = page.locator("#authModalLabel")

    expect(auth_modal).to_be_visible()
    expect(modal_title).to_have_text("Join our community!")


@qase.id(62)
def test_should_show_auth_modal_when_guest_clicks_save_button_in_latest_section(page: Page, live_server, seeded_recipe):
    page.goto(live_server.url)

    recent_wrapper = page.locator("#recent-wrapper")
    save_icon = recent_wrapper.locator("span[title='Save']").first
    save_icon.click()

    auth_modal = page.locator("#authModal")
    modal_title = page.locator("#authModalLabel")

    expect(auth_modal).to_be_visible()
    expect(modal_title).to_have_text("Join our community!")


@qase.id(63)
def test_should_display_view_all_link_in_latest_recipes_section(page: Page, live_server):
    page.goto(live_server.url)

    view_all_latest_link = page.locator("#viewAllLatestBtn")
    expect(view_all_latest_link).to_be_visible()
    expect(view_all_latest_link).to_be_enabled()
    expect(view_all_latest_link).to_have_text("View All →")


# ==========================================
# TEST SUITE: HOME PAGE FILTERING
# ==========================================
@qase.id(64)
def test_should_hide_saved_recipes_section_from_unauthenticated_user(page: Page, live_server):
    page.goto(live_server.url)

    saved_recipes_heading = page.get_by_role("heading", name="Saved Recipes", exact=True)
    saved_wrapper = page.locator("#dynamic-saved-wrapper")

    expect(saved_recipes_heading).not_to_be_attached()
    expect(saved_wrapper).not_to_be_attached()


@qase.id(65)
def test_should_filter_recipes_when_exact_ingredient_name_is_searched(page: Page, live_server,
                                                                      seeded_recipes_for_filtering):
    page.goto(live_server.url)

    ingredient_input = page.locator("#ingredientSearchInput")
    search_btn = page.locator("#ingredientSearchBtn")
    trending_wrapper = page.locator("#trending-wrapper")

    ingredient_input.fill("cassava")

    # INTERCEPT: Wait deterministically for AJAX response
    with page.expect_response("**/api/filter-home/**") as response_info:
        search_btn.click()
    assert response_info.value.ok

    expect(trending_wrapper.locator("text=Cassava Cake")).to_be_visible()
    expect(trending_wrapper.locator("text=American Burger")).not_to_be_visible()


@qase.id(66)
def test_should_filter_recipes_when_partial_ingredient_name_is_searched(page: Page, live_server,
                                                                        seeded_recipes_for_filtering):
    page.goto(live_server.url)

    ingredient_input = page.locator("#ingredientSearchInput")
    search_btn = page.locator("#ingredientSearchBtn")
    trending_wrapper = page.locator("#trending-wrapper")

    ingredient_input.fill("coco")  # Partial for coconut milk

    with page.expect_response("**/api/filter-home/**") as response_info:
        search_btn.click()
    assert response_info.value.ok

    expect(trending_wrapper.locator("text=Cassava Cake")).to_be_visible()
    expect(trending_wrapper.locator("text=American Burger")).not_to_be_visible()


@qase.id(67)
def test_should_filter_recipes_when_multiple_ingredients_are_searched_with_comma_separation(page: Page, live_server,
                                                                                            seeded_recipes_for_filtering):
    page.goto(live_server.url)

    ingredient_input = page.locator("#ingredientSearchInput")
    search_btn = page.locator("#ingredientSearchBtn")
    trending_wrapper = page.locator("#trending-wrapper")

    ingredient_input.fill("cassava, sugar")

    with page.expect_response("**/api/filter-home/**") as response_info:
        search_btn.click()
    assert response_info.value.ok

    expect(trending_wrapper.locator("text=Cassava Cake")).to_be_visible()
    expect(trending_wrapper.locator("text=American Burger")).not_to_be_visible()


@qase.id(68)
def test_should_filter_recipes_when_existing_country_is_selected(page: Page, live_server, seeded_recipes_for_filtering):
    page.goto(live_server.url)

    country_btn = page.locator("#countryFilterBtn")
    country_search_input = page.locator("#countrySearchInput")
    country_list = page.locator("#countryDropdownList")
    trending_wrapper = page.locator("#trending-wrapper")

    country_btn.click()
    country_search_input.fill("Vietnam")

    with page.expect_response("**/api/filter-home/**") as response_info:
        country_list.get_by_role("button", name="Vietnam").click()
    assert response_info.value.ok

    expect(country_btn).to_have_class(re.compile(r"btn-success"))
    expect(trending_wrapper.locator("text=Cassava Cake")).to_be_visible()
    expect(trending_wrapper.locator("text=American Burger")).not_to_be_visible()


@qase.id(69)
def test_should_filter_recipes_when_existing_category_tag_is_selected(page: Page, live_server,
                                                                      seeded_recipes_for_filtering):
    page.goto(live_server.url)

    tag_btn = page.locator("#tagFilterBtn")
    tag_list = page.locator("ul[aria-labelledby='tagFilterBtn']")
    trending_wrapper = page.locator("#trending-wrapper")

    tag_btn.click()

    with page.expect_response("**/api/filter-home/**") as response_info:
        tag_list.get_by_role("button", name="Dessert").click()
    assert response_info.value.ok

    expect(tag_btn).to_have_class(re.compile(r"btn-success"))
    expect(trending_wrapper.locator("text=Cassava Cake")).to_be_visible()
    expect(trending_wrapper.locator("text=American Burger")).not_to_be_visible()


@qase.id(70)
def test_should_filter_recipes_when_most_liked_is_toggled(page: Page, live_server, seeded_recipes_for_filtering):
    # ---------------------------------------------------------
    # PRE-ACTION: Login and Like a recipe via UI to sync state
    # ---------------------------------------------------------
    page.goto(f"{live_server.url}/login/")

    # Fill login form
    page.locator('input[name="username"]').fill('testautomation')
    page.locator('input[name="password"]').fill('StrongTestPassword123!')
    page.get_by_role("button", name="Login", exact=True).click()

    # Wait for redirect to Home Page
    expect(page).to_have_url(f"{live_server.url}/")

    # Find the American Burger card in Trending and Like it
    trending_wrapper = page.locator("#trending-wrapper")
    burger_card = trending_wrapper.locator(".scrolling-card", has_text="American Burger")
    like_btn = burger_card.locator("span[title='Like']")

    with page.expect_response("**/like/**") as response_info:
        like_btn.click()
    assert response_info.value.ok

    # Verify like was successful before proceeding
    expect(burger_card.locator(".bi-hand-thumbs-up-fill")).to_be_visible()

    # Logout to return to Guest state
    user_dropdown = page.locator("#userDropdown")
    user_dropdown.click()
    page.get_by_role("button", name="Logout").click()

    # Ensure returned to login screen, then go back to home as Guest
    expect(page).to_have_url(f"{live_server.url}/login/")
    page.goto(live_server.url)

    # ---------------------------------------------------------
    # MAIN TEST: Guest testing the Most Liked filter
    # ---------------------------------------------------------
    most_liked_btn = page.locator("#mostLikedBtn")
    trending_wrapper = page.locator("#trending-wrapper")

    with page.expect_response("**/api/filter-home/**") as response_info:
        most_liked_btn.click()
    assert response_info.value.ok

    # Assertions
    expect(most_liked_btn).to_have_class(re.compile(r"btn-success"))
    expect(trending_wrapper.locator("text=American Burger")).to_be_visible()


@qase.id(71)
def test_should_filter_recipes_when_existing_author_is_selected(page: Page, live_server, test_user,
                                                                seeded_recipes_for_filtering):
    page.goto(live_server.url)

    author_btn = page.locator("#authorFilterBtn")
    author_search_input = page.locator("#authorSearchInput")
    author_list = page.locator("#authorDropdownList")
    trending_wrapper = page.locator("#trending-wrapper")

    author_btn.click()
    author_search_input.fill(test_user.username)

    with page.expect_response("**/api/filter-home/**") as response_info:
        author_list.get_by_role("button", name=test_user.username).click()
    assert response_info.value.ok

    expect(author_btn).to_have_class(re.compile(r"btn-success"))
    expect(trending_wrapper.locator("text=Cassava Cake")).to_be_visible()
    expect(trending_wrapper.locator("text=American Burger")).to_be_visible()


@qase.id(72)
def test_should_clear_country_filter_when_refresh_button_is_clicked(page: Page, live_server,
                                                                    seeded_recipes_for_filtering):
    page.goto(live_server.url)

    country_btn = page.locator("#countryFilterBtn")
    country_list = page.locator("#countryDropdownList")
    refresh_btn = page.locator("#refreshFilterBtn")
    trending_wrapper = page.locator("#trending-wrapper")

    # Apply filter first
    country_btn.click()
    page.locator("#countrySearchInput").fill("Vietnam")
    with page.expect_response("**/api/filter-home/**"):
        country_list.get_by_role("button", name="Vietnam").click()
    expect(trending_wrapper.locator("text=American Burger")).not_to_be_visible()

    # Refresh and intercept
    with page.expect_response("**/api/filter-home/**") as response_info:
        refresh_btn.click()
    assert response_info.value.ok

    expect(country_btn).not_to_have_class(re.compile(r"btn-success"))
    expect(country_btn).to_have_text("Country")
    expect(trending_wrapper.locator("text=American Burger")).to_be_visible()


@qase.id(73)
def test_should_clear_category_tag_filter_when_refresh_button_is_clicked(page: Page, live_server,
                                                                         seeded_recipes_for_filtering):
    page.goto(live_server.url)

    tag_btn = page.locator("#tagFilterBtn")
    refresh_btn = page.locator("#refreshFilterBtn")
    trending_wrapper = page.locator("#trending-wrapper")

    tag_btn.click()
    with page.expect_response("**/api/filter-home/**"):
        page.locator("ul[aria-labelledby='tagFilterBtn']").get_by_role("button", name="Dessert").click()

    with page.expect_response("**/api/filter-home/**") as response_info:
        refresh_btn.click()
    assert response_info.value.ok

    expect(tag_btn).not_to_have_class(re.compile(r"btn-success"))
    expect(tag_btn).to_have_text("Category Tag")
    expect(trending_wrapper.locator("text=American Burger")).to_be_visible()


@qase.id(74)
def test_should_clear_most_liked_filter_when_refresh_button_is_clicked(page: Page, live_server,
                                                                       seeded_recipes_for_filtering):
    page.goto(live_server.url)

    most_liked_btn = page.locator("#mostLikedBtn")
    refresh_btn = page.locator("#refreshFilterBtn")

    with page.expect_response("**/api/filter-home/**"):
        most_liked_btn.click()

    with page.expect_response("**/api/filter-home/**") as response_info:
        refresh_btn.click()
    assert response_info.value.ok

    expect(most_liked_btn).not_to_have_class(re.compile(r"btn-success"))


@qase.id(75)
def test_should_clear_author_filter_when_refresh_button_is_clicked(page: Page, live_server, test_user,
                                                                   seeded_recipes_for_filtering):
    page.goto(live_server.url)

    author_btn = page.locator("#authorFilterBtn")
    refresh_btn = page.locator("#refreshFilterBtn")

    author_btn.click()
    page.locator("#authorSearchInput").fill(test_user.username)
    with page.expect_response("**/api/filter-home/**"):
        page.locator("#authorDropdownList").get_by_role("button", name=test_user.username).click()

    with page.expect_response("**/api/filter-home/**") as response_info:
        refresh_btn.click()
    assert response_info.value.ok

    expect(author_btn).not_to_have_class(re.compile(r"btn-success"))
    expect(author_btn).to_have_text("Posted By")


@qase.id(76)
def test_should_retain_ingredient_search_value_and_results_when_refresh_button_is_clicked(page: Page, live_server,
                                                                                          seeded_recipes_for_filtering):
    page.goto(live_server.url)

    ingredient_input = page.locator("#ingredientSearchInput")
    search_btn = page.locator("#ingredientSearchBtn")
    refresh_btn = page.locator("#refreshFilterBtn")
    trending_wrapper = page.locator("#trending-wrapper")

    ingredient_input.fill("cassava")
    with page.expect_response("**/api/filter-home/**"):
        search_btn.click()

    with page.expect_response("**/api/filter-home/**") as response_info:
        refresh_btn.click()
    assert response_info.value.ok

    expect(ingredient_input).to_have_value("cassava")
    expect(trending_wrapper.locator("text=American Burger")).not_to_be_visible()


@qase.id(28)
def test_should_display_empty_state_when_nonexistent_ingredient_is_searched(page: Page, live_server,
                                                                            seeded_recipes_for_filtering):
    page.goto(live_server.url)

    ingredient_input = page.locator("#ingredientSearchInput")
    search_btn = page.locator("#ingredientSearchBtn")
    trending_wrapper = page.locator("#trending-wrapper")

    ingredient_input.fill("dragonfruit")

    with page.expect_response("**/api/filter-home/**") as response_info:
        search_btn.click()
    assert response_info.value.ok

    # Asserting count(0) for deterministic empty state check without relying on emojis
    expect(trending_wrapper.locator(".scrolling-card")).to_have_count(0)


@qase.id(31)
def test_should_display_empty_state_when_nonexistent_country_is_selected(page: Page, live_server,
                                                                         seeded_recipes_for_filtering):
    page.goto(live_server.url)

    country_btn = page.locator("#countryFilterBtn")
    country_search_input = page.locator("#countrySearchInput")
    country_list = page.locator("#countryDropdownList")
    trending_wrapper = page.locator("#trending-wrapper")

    country_btn.click()
    country_search_input.fill("Brazil")

    with page.expect_response("**/api/filter-home/**") as response_info:
        country_list.get_by_role("button", name="Brazil").click()
    assert response_info.value.ok

    expect(trending_wrapper.locator(".scrolling-card")).to_have_count(0)


@qase.id(33)
def test_should_display_empty_state_when_nonexistent_category_tag_is_selected(page: Page, live_server,
                                                                              seeded_recipes_for_filtering):
    page.goto(live_server.url)

    tag_btn = page.locator("#tagFilterBtn")
    tag_list = page.locator("ul[aria-labelledby='tagFilterBtn']")
    trending_wrapper = page.locator("#trending-wrapper")

    tag_btn.click()

    with page.expect_response("**/api/filter-home/**") as response_info:
        tag_list.get_by_role("button", name="Refresher").click()
    assert response_info.value.ok

    expect(trending_wrapper.locator(".scrolling-card")).to_have_count(0)


@qase.id(35)
def test_should_display_empty_state_when_nonexistent_most_liked_is_toggled(page: Page, live_server):
    # Setup specific DB state: No recipes are liked
    page.goto(live_server.url)

    most_liked_btn = page.locator("#mostLikedBtn")
    trending_wrapper = page.locator("#trending-wrapper")

    with page.expect_response("**/api/filter-home/**") as response_info:
        most_liked_btn.click()
    assert response_info.value.ok

    expect(trending_wrapper.locator(".scrolling-card")).to_have_count(0)


@qase.id(37)
def test_should_display_all_recipes_when_ingredient_search_is_submitted_empty(page: Page, live_server,
                                                                              seeded_recipes_for_filtering):
    page.goto(live_server.url)

    ingredient_input = page.locator("#ingredientSearchInput")
    search_btn = page.locator("#ingredientSearchBtn")
    trending_wrapper = page.locator("#trending-wrapper")

    ingredient_input.fill("")

    with page.expect_response("**/api/filter-home/**") as response_info:
        search_btn.click()
    assert response_info.value.ok

    expect(trending_wrapper.locator("text=Cassava Cake")).to_be_visible()
    expect(trending_wrapper.locator("text=American Burger")).to_be_visible()
