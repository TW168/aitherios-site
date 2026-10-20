"""
Create the starting content for a fresh site:

- the three languages (English, Traditional Chinese, Spanish)
- the home page, the Projects page and the Video Analysis project
- Chinese and Spanish translations of those pages, made through
  wagtail-localize so editors can keep editing them side by side

Safe to run more than once: it does nothing if a home page already exists.

    python manage.py setup_site
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.models import Locale, Page, Site
from wagtail_localize.models import StringTranslation, Translation, TranslationSource

from home.models import FeaturedProject, HomePage, ProjectIndexPage, ProjectPage

# Starting text. Bracketed values are placeholders for the owner to replace.
TEXT = {
    "home_title": "Home",
    "kicker": "Personal projects",
    "tagline": "[Your tagline]",
    "button": "Explore projects",
    "intro_heading": "About this site",
    "intro": "<p>[Introduction: what aitherios means and what this site is for]</p>",
    "projects_heading": "Featured projects",
    "projects_title": "Projects",
    "va_title": "Video Analysis",
    "va_summary": "Upload a short video and the system identifies the objects in it.",
    "va_body": "<p>[Project description]</p>",
}

TRANSLATIONS = {
    "zh-hant": {
        "Home": "首頁",
        "Personal projects": "個人專案",
        "[Your tagline]": "[您的標語]",
        "Explore projects": "探索專案",
        "About this site": "關於本站",
        "[Introduction: what aitherios means and what this site is for]": "[簡介：aitherios 的含義與本站用途]",
        "Featured projects": "精選專案",
        "Projects": "專案",
        "Video Analysis": "影片分析",
        "Upload a short video and the system identifies the objects in it.": "上傳一段短片，系統會辨識影片中的物件。",
        "[Project description]": "[專案說明]",
    },
    "es": {
        "Home": "Inicio",
        "Personal projects": "Proyectos personales",
        "[Your tagline]": "[Tu eslogan]",
        "Explore projects": "Explorar proyectos",
        "About this site": "Acerca de este sitio",
        "[Introduction: what aitherios means and what this site is for]": "[Introducción: qué significa aitherios y para qué sirve este sitio]",
        "Featured projects": "Proyectos destacados",
        "Projects": "Proyectos",
        "Video Analysis": "Análisis de video",
        "Upload a short video and the system identifies the objects in it.": "Sube un video corto y el sistema identifica los objetos que aparecen en él.",
        "[Project description]": "[Descripción del proyecto]",
    },
}

# Slugs stay the same in every language so URLs line up: /en/projects/, /es/projects/ …


class Command(BaseCommand):
    help = "Create the starting pages and their Chinese and Spanish translations."

    def handle(self, *args, **options):
        if HomePage.objects.exists():
            self.stdout.write("A home page already exists; nothing to do.")
            return

        with transaction.atomic():
            self._build()
            # Wagtail finishes publishing in on-commit callbacks, and publishing a
            # translated parent in the same transaction as its children leaves a
            # stale child count (children then 404). Recount the tree after those
            # callbacks have run.
            transaction.on_commit(Page.fix_tree)

        self.stdout.write(self.style.SUCCESS("Site created in English, Traditional Chinese and Spanish."))

    def _build(self):

        locales = {code: Locale.objects.get_or_create(language_code=code)[0] for code, _ in settings.LANGUAGES}
        en = locales[settings.LANGUAGE_CODE]

        root = Page.get_first_root_node()
        home = root.add_child(
            instance=HomePage(
                title=TEXT["home_title"],
                slug="home-new",
                locale=en,
                hero_kicker=TEXT["kicker"],
                hero_tagline=TEXT["tagline"],
                hero_button_text=TEXT["button"],
                intro_heading=TEXT["intro_heading"],
                intro=TEXT["intro"],
                projects_heading=TEXT["projects_heading"],
            )
        )

        # Point the site at the new home page and remove Wagtail's welcome page.
        site = Site.objects.filter(is_default_site=True).first()
        old_root = site.root_page if site else None
        if site:
            site.root_page = home
            site.site_name = "aitherios"
            site.save()
        else:
            Site.objects.create(hostname="localhost", root_page=home, is_default_site=True, site_name="aitherios")
        if old_root and old_root.pk != home.pk:
            old_root.delete()
        home.slug = "home"
        home.save()

        projects = home.add_child(
            instance=ProjectIndexPage(title=TEXT["projects_title"], slug="projects", show_in_menus=True, locale=en)
        )
        video = projects.add_child(
            instance=ProjectPage(
                title=TEXT["va_title"],
                slug="video-analysis",
                summary=TEXT["va_summary"],
                body=TEXT["va_body"],
                locale=en,
            )
        )
        for page in (home, projects, video):
            page.save_revision().publish()

        home.featured_projects.add(FeaturedProject(project=video, sort_order=0))
        home.save_revision().publish()

        # Translations, parents before children.
        for code, strings in TRANSLATIONS.items():
            for page in (home, projects, video):
                self._translate(page.specific, locales[code], strings)

    def _translate(self, page, locale, strings):
        source, _ = TranslationSource.get_or_create_from_instance(page)
        translation, _ = Translation.objects.get_or_create(
            source=source, target_locale=locale, defaults={"enabled": True}
        )
        for segment in source.stringsegment_set.select_related("string", "context"):
            text = segment.string.data
            translated = strings.get(text, text)
            StringTranslation.objects.update_or_create(
                translation_of=segment.string,
                locale=locale,
                context=segment.context,
                defaults={"data": translated},
            )
        translation.save_target(publish=True)
