from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, PageChooserPanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page

RICH_TEXT_FEATURES = ["h2", "h3", "bold", "italic", "link", "ol", "ul"]


class HomePage(Page):
    """The landing page. One per language."""

    hero_kicker = models.CharField(
        max_length=80, blank=True, help_text="Small line above the site name, e.g. 'Personal projects'."
    )
    hero_tagline = models.CharField(max_length=200, blank=True)
    hero_button_text = models.CharField(max_length=40, default="Explore projects")
    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Background image. Wide (at least 1920 px) and dark works best.",
    )
    hero_video = models.ForeignKey(
        "wagtaildocs.Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Optional background video (.mp4 or .webm, short and muted). Overrides the image.",
    )
    intro_heading = models.CharField(max_length=120, default="About this site")
    intro = RichTextField(features=RICH_TEXT_FEATURES, blank=True)
    projects_heading = models.CharField(max_length=120, default="Featured projects")

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("hero_kicker"),
                FieldPanel("hero_tagline"),
                FieldPanel("hero_button_text"),
                FieldPanel("hero_image"),
                FieldPanel("hero_video"),
            ],
            heading="Hero",
        ),
        MultiFieldPanel([FieldPanel("intro_heading"), FieldPanel("intro")], heading="Introduction"),
        MultiFieldPanel(
            [FieldPanel("projects_heading"), InlinePanel("featured_projects", label="Featured project")],
            heading="Featured projects",
        ),
    ]

    parent_page_types = ["wagtailcore.Page"]
    subpage_types = ["home.ProjectIndexPage"]
    max_count_per_parent = 1

    class Meta:
        verbose_name = "Home page"

    def get_featured_projects(self):
        projects = []
        for item in self.featured_projects.select_related("project"):
            if item.project and item.project.live:
                page = item.project.specific.localized
                if page.live:
                    projects.append(page)
        return projects


class FeaturedProject(Orderable):
    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="featured_projects")
    project = models.ForeignKey("wagtailcore.Page", on_delete=models.CASCADE, related_name="+")

    panels = [PageChooserPanel("project", page_type="home.ProjectPage")]


class ProjectIndexPage(Page):
    """Lists all projects. Linked from the navbar as 'Projects'."""

    intro = RichTextField(features=RICH_TEXT_FEATURES, blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro")]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.ProjectPage"]
    max_count_per_parent = 1

    class Meta:
        verbose_name = "Project index page"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["projects"] = ProjectPage.objects.child_of(self).live().order_by("path")
        return context


class ProjectPage(Page):
    """One showcased project, e.g. Video Analysis."""

    summary = models.CharField(max_length=255, help_text="One line, shown on project cards.")
    card_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    body = RichTextField(features=RICH_TEXT_FEATURES + ["image", "embed"], blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("summary"),
        FieldPanel("card_image"),
        FieldPanel("body"),
    ]

    parent_page_types = ["home.ProjectIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Project page"


@register_setting(icon="link")
class FooterSettings(BaseGenericSetting):
    """Footer links, shared by every page and language."""

    github_url = models.URLField(blank=True, verbose_name="GitHub URL")
    email = models.EmailField(blank=True)

    panels = [FieldPanel("github_url"), FieldPanel("email")]

    class Meta:
        verbose_name = "Footer"
