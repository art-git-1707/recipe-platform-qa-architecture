import re
import pytest
from playwright.sync_api import Page, expect, BrowserContext
from recipes.models import Recipe
from django.urls import reverse
from qase.pytest import qase

# ==========================================
# FIXTURES (SETUP DATA)
# ==========================================
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
# TEST AUTOMATION SUITE: RECIPE DETAILS & GUEST FLOWS
# ==========================================

@qase.id(77)
def test_should_open_recipe_details_when_guest_clicks_trending_recipe_card(page: Page, live_server, sample_recipe):
    page.goto(live_server.url + '/')

    recipe_card = page.locator(f"#trending-wrapper .scrolling-card:has-text('{sample_recipe.title}')").first
    expect(recipe_card).to_be_visible()
    recipe_card.click()

    expect(page).to_have_url(re.compile(rf"/recipe/{sample_recipe.hashid}/"))
    expect(page.locator("h1.display-5")).to_have_text(sample_recipe.title)


@qase.id(78)
def test_should_open_recipe_details_when_guest_clicks_latest_recipe_card(page: Page, live_server, sample_recipe):
    page.goto(live_server.url + '/')

    recipe_card = page.locator(f"#recent-wrapper .scrolling-card:has-text('{sample_recipe.title}')").first
    expect(recipe_card).to_be_visible()
    recipe_card.click()

    expect(page).to_have_url(re.compile(rf"/recipe/{sample_recipe.hashid}/"))
    expect(page.locator("h1.display-5")).to_have_text(sample_recipe.title)


@qase.id(79)
def test_should_display_recipe_details_when_guest_navigates_via_direct_url(page: Page, live_server, sample_recipe):
    page.goto(live_server.url + f'/recipe/{sample_recipe.hashid}/')

    expect(page.locator("h1.display-5")).to_have_text(sample_recipe.title)
    expect(page.locator(".badge.bg-secondary")).to_contain_text(sample_recipe.author.username)


@qase.id(80)
def test_should_redirect_to_latest_recipes_list_when_guest_clicks_view_all_latest_button(page: Page, live_server):
    page.goto(live_server.url + '/')

    view_all_btn = page.locator("id=viewAllLatestBtn")
    expect(view_all_btn).to_be_visible()
    view_all_btn.click()

    expect(page).to_have_url(re.compile(r"/latest/"))


@qase.id(81)
def test_should_navigate_to_search_results_when_guest_searches_exact_recipe_name(page: Page, live_server,
                                                                                 sample_recipe):
    page.goto(live_server.url + '/')

    search_input = page.locator('input[type="search"][name="q"]')
    search_input.fill(sample_recipe.title)
    search_input.press("Enter")

    expect(page).to_have_url(re.compile(r"/latest/.*q="))

    result_card = page.locator(f".card:has-text('{sample_recipe.title}')").first
    expect(result_card).to_be_visible()
    result_card.click()

    expect(page).to_have_url(re.compile(rf"/recipe/{sample_recipe.hashid}/"))


@qase.id(82)
def test_should_navigate_to_search_results_when_guest_searches_partial_recipe_name(page: Page, live_server,
                                                                                   sample_recipe):
    page.goto(live_server.url + '/')

    partial_name = sample_recipe.title.split()[0]
    search_input = page.locator('input[type="search"][name="q"]')
    search_input.fill(partial_name)
    search_input.press("Enter")

    expect(page).to_have_url(re.compile(r"/latest/.*q="))

    result_card = page.locator(f".card:has-text('{sample_recipe.title}')").first
    expect(result_card).to_be_visible()
    result_card.click()

    expect(page).to_have_url(re.compile(rf"/recipe/{sample_recipe.hashid}/"))


@qase.id(83)
def test_should_trigger_auth_modal_when_unauthenticated_guest_clicks_like_button(page: Page, live_server,
                                                                                 sample_recipe):
    page.goto(live_server.url + f'/recipe/{sample_recipe.hashid}/')

    like_btn = page.locator('button[title="Like"]')
    expect(like_btn).to_be_visible()
    like_btn.click()

    auth_modal = page.locator("id=authModal")
    expect(auth_modal).to_be_visible()
    expect(auth_modal.locator("id=authModalLabel")).to_have_text("Join our community!")


@qase.id(84)
def test_should_trigger_auth_modal_when_unauthenticated_guest_clicks_save_button(page: Page, live_server,
                                                                                 sample_recipe):
    page.goto(live_server.url + f'/recipe/{sample_recipe.hashid}/')

    save_btn = page.locator('button[title="Save"]')
    expect(save_btn).to_be_visible()
    save_btn.click()

    auth_modal = page.locator("id=authModal")
    expect(auth_modal).to_be_visible()
    expect(auth_modal.locator("id=authModalLabel")).to_have_text("Join our community!")


@qase.id(85)
def test_should_copy_link_to_clipboard_and_update_button_text_when_guest_clicks_share(page: Page,
                                                                                      context: BrowserContext,
                                                                                      live_server, sample_recipe):
    context.grant_permissions(["clipboard-read", "clipboard-write"])

    target_url = live_server.url + f'/recipe/{sample_recipe.hashid}/'
    page.goto(target_url)

    share_btn = page.locator('button[title="Copy Link to Share"]')
    expect(share_btn).to_be_visible()
    share_btn.click()

    share_text = share_btn.locator(".share-text")
    expect(share_text).to_have_text("Copied!")
    expect(share_text).to_have_class(re.compile(r"text-success"))

    clipboard_content = page.evaluate("navigator.clipboard.readText()")
    assert clipboard_content == target_url


@qase.id(86)
def test_should_hide_recipe_action_menu_when_user_is_unauthenticated_guest(page: Page, live_server, sample_recipe):
    page.goto(live_server.url + f'/recipe/{sample_recipe.hashid}/')

    action_menu = page.locator("id=recipeActionMenu")
    expect(action_menu).not_to_be_attached()


@qase.id(87)
def test_should_deny_edit_access_when_unauthenticated_guest_navigates_to_edit_url(page: Page, live_server,
                                                                                  sample_recipe):
    page.goto(live_server.url + f'/recipe/{sample_recipe.hashid}/edit/')

    expect(page).to_have_url(re.compile(r"/login/"))


@qase.id(88)
def test_should_deny_delete_access_when_unauthenticated_guest_navigates_to_delete_url(page: Page, live_server,
                                                                                      sample_recipe):
    page.goto(live_server.url + f'/recipe/{sample_recipe.hashid}/delete/')

    expect(page).to_have_url(re.compile(r"/login/"))


@qase.id(89)
def test_should_display_all_ingredients_when_guest_views_recipe_details(page: Page, live_server, sample_recipe):
    page.goto(live_server.url + f'/recipe/{sample_recipe.hashid}/')

    ingredients_list = page.locator("id=ingredients-ui-list")
    expect(ingredients_list).to_be_visible()

    ingredients = sample_recipe.ingredients.split('\n')
    for ingredient in ingredients:
        if ingredient.strip():
            expect(ingredients_list).to_contain_text(ingredient.strip())


@qase.id(90)
def test_should_display_all_instructions_when_guest_views_recipe_details(page: Page, live_server, sample_recipe):
    page.goto(live_server.url + f'/recipe/{sample_recipe.hashid}/')

    instructions_list = page.locator("id=instructions-ui-list")
    expect(instructions_list).to_be_visible()

    instructions = sample_recipe.instructions.split('\n')
    for instruction in instructions:
        if instruction.strip():
            expect(instructions_list).to_contain_text(instruction.strip())


@qase.id(91)
def test_should_display_consistent_total_likes_between_home_page_and_recipe_details(page: Page, live_server,
                                                                                    sample_recipe):
    page.goto(live_server.url + '/')

    home_like_count_element = page.locator(f".like-count-{sample_recipe.hashid}").first
    expect(home_like_count_element).to_be_visible()
    home_likes = home_like_count_element.inner_text()

    page.goto(live_server.url + f'/recipe/{sample_recipe.hashid}/')

    detail_like_count_element = page.locator(f".like-count-{sample_recipe.hashid}").first
    expect(detail_like_count_element).to_be_visible()
    detail_likes = detail_like_count_element.inner_text()

    assert home_likes == detail_likes


@qase.id(92)
def test_should_display_consistent_total_saves_between_home_page_and_recipe_details(page: Page, live_server,
                                                                                    sample_recipe):
    page.goto(live_server.url + '/')

    home_save_count_element = page.locator(f".save-count-{sample_recipe.hashid}").first
    expect(home_save_count_element).to_be_visible()
    home_saves = home_save_count_element.inner_text()

    page.goto(live_server.url + f'/recipe/{sample_recipe.hashid}/')

    detail_save_count_element = page.locator(f".save-count-{sample_recipe.hashid}").first
    expect(detail_save_count_element).to_be_visible()
    detail_saves = detail_save_count_element.inner_text()

    assert home_saves == detail_saves
