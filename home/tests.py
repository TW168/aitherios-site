"""
Tests for the home page phase.

Run with:  python manage.py test
Each test maps to an acceptance criterion in the home page spec.
"""

import re
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from wagtail.models import Locale, Page
from wagtail.test.utils import WagtailPageTestCase

from home.models import FeaturedProject, FooterSettings, HomePage, ProjectIndexPage, ProjectPage

LANGS = ["en", "zh-hant", "es"]


def nav_text(html):
    """Visible text of the navbar links (not the language switch)."""
    block = re.search(r'class="navbar__links">(.*?)</ul>', html, re.S).group(1)
    return [t.strip() for t in re.findall(r">([^<>]+)</a>", block)]


@override_settings(ALLOWED_HOSTS=["testserver", "localhost"])
class SiteSetupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Translations are finished in on-commit callbacks; run them inside the test transaction.
        with cls.captureOnCommitCallbacks(execute=True):
            call_command("setup_site", stdout=StringIO())

    def get(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)
        return response.content.decode()

    # --- Content structure ----------------------------------------------

    def test_three_languages_exist(self):
        self.assertEqual(
            sorted(Locale.objects.values_list("language_code", flat=True)), sorted(LANGS)
        )

    def test_every_page_exists_in_every_language(self):
        for model in (HomePage, ProjectIndexPage, ProjectPage):
            codes = sorted(model.objects.live().values_list("locale__language_code", flat=True))
            self.assertEqual(codes, sorted(LANGS), model.__name__)

    def test_setup_is_safe_to_run_twice(self):
        call_command("setup_site", stdout=StringIO())
        self.assertEqual(HomePage.objects.count(), 3)

    def test_tree_is_consistent(self):
        self.assertEqual(Page.find_problems(), ([], [], [], [], []))

    # --- URLs and language -----------------------------------------------

    def test_root_redirects_to_a_language(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/en/")

    def test_all_pages_load_in_all_languages(self):
        for lang in LANGS:
            for path in ("", "projects/", "projects/video-analysis/"):
                self.get(f"/{lang}/{path}")

    def test_html_lang_attribute_matches_language(self):
        for lang in LANGS:
            self.assertIn(f'<html lang="{lang}">', self.get(f"/{lang}/"))

    def test_language_switch_keeps_the_same_page(self):
        html = self.get("/es/projects/video-analysis/")
        switch = re.search(r'class="lang-switch".*?</ul>', html, re.S).group(0)
        self.assertEqual(
            re.findall(r'href="([^"]+)"', switch),
            [
                "/en/projects/video-analysis/",
                "/zh-hant/projects/video-analysis/",
                "/es/projects/video-analysis/",
            ],
        )
        self.assertIn('aria-current="true" class="is-active">ES<', switch)

    def test_chinese_text_is_stored_and_shown_correctly(self):
        page = ProjectPage.objects.get(locale__language_code="zh-hant")
        self.assertEqual(page.title, "影片分析")
        self.assertIn("影片分析", self.get("/zh-hant/"))

    def test_interface_text_is_translated(self):
        self.assertIn("聯絡", self.get("/zh-hant/"))
        self.assertIn("Contacto", self.get("/es/"))
        self.assertIn("Ver proyecto", self.get("/es/"))

    # --- Navbar -----------------------------------------------------------

    def test_navbar_has_projects_and_contact_only(self):
        expected = {"en": ["Projects", "Contact"], "zh-hant": ["專案", "聯絡"], "es": ["Proyectos", "Contacto"]}
        for lang, items in expected.items():
            self.assertEqual(nav_text(self.get(f"/{lang}/")), items, lang)

    def test_navbar_never_lists_home_or_about(self):
        items = nav_text(self.get("/en/projects/"))
        self.assertNotIn("Home", items)
        self.assertNotIn("About", items)

    def test_navbar_follows_show_in_menus(self):
        ProjectIndexPage.objects.filter(locale__language_code="en").update(show_in_menus=False)
        self.assertEqual(nav_text(self.get("/en/")), ["Contact"])

    # --- Home page sections ----------------------------------------------

    def test_home_sections_in_order(self):
        html = self.get("/en/")
        positions = [html.index(marker) for marker in ('class="navbar"', 'class="hero"', 'id="about"', 'id="projects"', 'id="footer"')]
        self.assertEqual(positions, sorted(positions))

    def test_featured_project_card_is_localized(self):
        html = self.get("/zh-hant/")
        self.assertIn('href="/zh-hant/projects/video-analysis/"', html)
        self.assertIn("上傳一段短片", html)

    def test_unpublished_featured_project_is_hidden(self):
        ProjectPage.objects.get(locale__language_code="en").unpublish()
        self.assertNotIn("card__title", self.get("/en/"))

    def test_editor_changes_show_on_page(self):
        home = HomePage.objects.get(locale__language_code="en")
        home.hero_tagline = "Things I build"
        home.save_revision().publish()
        self.assertIn("Things I build", self.get("/en/"))

    # --- Footer -------------------------------------------------------------

    def test_footer_links_come_from_settings(self):
        html = self.get("/en/")
        self.assertNotIn("GitHub", html)
        settings_obj = FooterSettings.load()
        settings_obj.github_url = "https://github.com/tw168"
        settings_obj.email = "hello@example.com"
        settings_obj.save()
        html = self.get("/en/")
        self.assertIn('href="https://github.com/tw168"', html)
        self.assertIn('href="mailto:hello@example.com"', html)

    def test_missing_page_returns_404(self):
        response = self.client.get("/en/does-not-exist/")
        self.assertEqual(response.status_code, 404)


class PageRulesTests(WagtailPageTestCase):
    """Editors can only create pages where they make sense."""

    def test_home_page_parent(self):
        self.assertAllowedParentPageTypes(HomePage, {Page})

    def test_projects_live_under_home(self):
        self.assertAllowedParentPageTypes(ProjectIndexPage, {HomePage})
        self.assertAllowedSubpageTypes(HomePage, {ProjectIndexPage})

    def test_project_pages_live_under_projects(self):
        self.assertAllowedParentPageTypes(ProjectPage, {ProjectIndexPage})
        self.assertAllowedSubpageTypes(ProjectPage, set())

    def test_featured_project_only_accepts_project_pages(self):
        panel = FeaturedProject.panels[0]
        self.assertEqual(panel.page_type, "home.ProjectPage")
