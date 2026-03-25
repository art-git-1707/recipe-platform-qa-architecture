import os
import sys
import asyncio
import pytest
from django.contrib.auth.models import User

# ==========================================
# 1. DJANGO & PLAYWRIGHT ASYNC COMPATIBILITY FIXES
# ==========================================
# Tell Django's ORM to relax its async-safety checks during testing
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# Force Windows to use ProactorEventLoop so Playwright can open the browser
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


# ==========================================
# 2. GLOBAL DATABASE ACCESS
# ==========================================
# Automatically grant database access to all tests so we don't have to add @pytest.mark.django_db everywhere
@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass

# ==========================================
# 3. PLAYWRIGHT BROWSER CONFIGURATION
# ==========================================
# Set default viewport size for all Playwright browser instances to simulate a standard desktop
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {
            "width": 1280,
            "height": 720,
        }
    }

# ==========================================
# 4. REUSABLE DATA FIXTURES
# ==========================================
# Create a standard dummy user that any test case can request and use
@pytest.fixture
def test_user():
    user = User.objects.create_user(
        username='testautomation',
        email='auto@isharerecipe.com',
        password='StrongTestPassword123!'
    )
    return user
