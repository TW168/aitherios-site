from django import template
from django.conf import settings
from django.utils import translation
from wagtail.models import Site

register = template.Library()

# Labels shown on the language switch buttons.
SHORT_NAMES = {"en": "EN", "zh-hant": "繁中", "es": "ES"}


def _site_root(request):
    site = Site.find_for_request(request) if request else None
    return site.root_page.specific if site else None


@register.simple_tag(takes_context=True)
def localized_home(context):
    """The home page in the current language (falls back to the site root)."""
    root = _site_root(context.get("request"))
    return root.localized if root else None


@register.simple_tag(takes_context=True)
def navbar_pages(context):
    """Live pages under the current language's home with 'Show in menus' ticked.

    The home page itself is never listed: the logo already links to it.
    """
    home = localized_home(context)
    if not home:
        return []
    return home.get_children().live().in_menu().specific()


@register.simple_tag(takes_context=True)
def language_links(context):
    """One link per site language, pointing at the same page in that language.

    If the current page has no translation in a language, the link goes to
    that language's home page instead.
    """
    request = context.get("request")
    page = context.get("page")
    current = translation.get_language()
    root = _site_root(request)

    translations = {}
    if page is not None:
        for p in page.get_translations(inclusive=True).live().select_related("locale"):
            translations[p.locale.language_code] = p
    home_by_lang = {}
    if root is not None:
        for p in root.get_translations(inclusive=True).live().select_related("locale"):
            home_by_lang[p.locale.language_code] = p

    links = []
    for code, name in settings.LANGUAGES:
        target = translations.get(code) or home_by_lang.get(code)
        url = target.get_url(request) if target else f"/{code}/"
        links.append(
            {
                "code": code,
                "name": name,
                "short": SHORT_NAMES.get(code, code),
                "url": url,
                "active": code == current,
            }
        )
    return links
