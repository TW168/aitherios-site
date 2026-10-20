# User guide — editing aitherios.cloud

Everything visitors see can be changed in the admin at **https://aitherios.cloud/admin/** without touching code.

## Signing in

Go to `/admin/` and sign in with the account made by `createsuperuser`. To add more editors, use **Settings → Users**.

## The pages

In the admin, open **Pages**. Each language has its own copy of the site:

- **Home**: English, at `/en/`
- **首頁**: Traditional Chinese, at `/zh-hant/`
- **Inicio**: Spanish, at `/es/`

Each one contains **Projects**, which contains **Video Analysis**.

## Editing the home page

Open **Pages → Home → Edit**. The fields are grouped:

| Group | Field | Shows up as |
| --- | --- | --- |
| Hero | Hero kicker | Small orange line above the site name |
| | Hero tagline | Line under the site name |
| | Hero button text | The orange button |
| | Hero image | Full-width background, at least 1920 px wide; dark images read best |
| | Hero video | Optional short muted background video (.mp4 or .webm). It replaces the image |
| Introduction | Intro heading, Intro | The "About this site" section |
| Featured projects | Projects heading, Featured project | The project cards, in the order listed |

Click **Publish** to make changes live, or **Save draft** to keep working. **Preview** shows the page before publishing.

To upload the hero video, add it under **Documents** first, then choose it in **Hero video**.

## Translating

Pages are linked across languages, so you translate rather than retype.

1. Edit the English page and publish it.
2. Open the Chinese or Spanish copy. It shows a side-by-side translation screen: English on the left, the translation on the right.
3. Fill in or correct each field and click **Publish**.
4. When the English page changes later, open it and choose **⋯ → Sync translated pages**, then update the translations.

Button labels such as "Contact" and "View project" are translated in the code, not in the admin. Ask the developer to change them.

## Adding a project

1. **Pages → Home → Projects → Add child page → Project page**.
2. Fill in **Title**, **Summary** (one line, shown on cards), **Card image** and **Body**.
3. Publish.
4. To translate it, open the page's **⋯** menu and choose **Translate**, then pick the languages.
5. To show it on the home page, edit **Home**, add a **Featured project**, choose it and publish.

## The navbar

The navbar shows every page directly under Home that has **Promote → Show in menus** ticked (currently **Projects**), plus **Contact**, which jumps to the footer. Home and About are intentionally not listed: the logo goes home, and About is a section of the home page.

## The footer

**Settings → Footer**: the GitHub URL and email. Leave a field empty to hide it.

## Images

Upload under **Images**. Use the focal point tool (click **Edit** on an image) so the important part isn't cropped on cards and the hero.

## Something looks wrong?

- **Change not showing:** check you clicked **Publish**, not only **Save draft**.
- **A language shows English text:** that translation hasn't been filled in yet. Open the page in that language and translate it.
- **A page shows "Page not found":** tell the developer. It is usually fixed with one command (`fixtree`).
