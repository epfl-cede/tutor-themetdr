from __future__ import annotations

import os
import typing as t
from glob import glob

import importlib_resources
from tutor import hooks
from tutor.__about__ import __version_suffix__
from tutormfe.hooks import PLUGIN_SLOTS

from .__about__ import __version__

# Handle version suffix in main mode, just like tutor core
if __version_suffix__:
    __version__ += "-" + __version_suffix__


################# Configuration
config: t.Dict[str, t.Dict[str, t.Any]] = {
    # Add here your new settings
    "defaults": {
        "VERSION": __version__,
        "WELCOME_MESSAGE": "The place for all your online learning",
        "PRIMARY_COLOR": "#15376D",  # TDR
        "ENABLE_DARK_TOGGLE": True,
        # Footer links are dictionaries with a "title" and "url"
        # To remove all links, run:
        # tutor config save --set THEMETDR_FOOTER_NAV_LINKS=[]
        "FOOTER_NAV_LINKS": [
            {"title": "About Us", "url": "/about"},
            {"title": "Terms of Service", "url": "/tos"},
            {"title": "Privacy Policy", "url": "/privacy"},
            {"title": "Help", "url": "/help"},
            {"title": "Contact Us", "url": "/contact"},
        ],
    },
    "unique": {},
    "overrides": {},
}

# Theme templates
hooks.Filters.ENV_TEMPLATE_ROOTS.add_item(
    str(importlib_resources.files("tutorthemetdr") / "templates")
)
# This is where the theme is rendered in the openedx build directory
hooks.Filters.ENV_TEMPLATE_TARGETS.add_items(
    [
        ("tdr", "build/openedx/themes"),
        ("tdr/env.config.jsx", "plugins/mfe/build/mfe"),
    ],
)

# Force the rendering of scss files, even though they are included in a "partials" directory
hooks.Filters.ENV_PATTERNS_INCLUDE.add_items(
    [
        r"tdr/lms/static/sass/partials/lms/theme/",
        r"tdr/cms/static/sass/partials/cms/theme/",
    ]
)


# init script: set theme automatically
with open(
    os.path.join(
        str(importlib_resources.files("tutorthemetdr") / "templates"),
        "tdr",
        "tasks",
        "init.sh",
    ),
    encoding="utf-8",
) as task_file:
    hooks.Filters.CLI_DO_INIT_TASKS.add_item(("lms", task_file.read()))


# Override openedx & mfe docker image names
@hooks.Filters.CONFIG_DEFAULTS.add(priority=hooks.priorities.LOW)
def _override_openedx_docker_image(
    items: list[tuple[str, t.Any]],
) -> list[tuple[str, t.Any]]:
    openedx_image = ""
    mfe_image = ""
    for k, v in items:
        if k == "DOCKER_IMAGE_OPENEDX":
            openedx_image = v
        elif k == "MFE_DOCKER_IMAGE":
            mfe_image = v
    if openedx_image:
        items.append(("DOCKER_IMAGE_OPENEDX", f"{openedx_image}-tdr"))
    if mfe_image:
        items.append(("MFE_DOCKER_IMAGE", f"{mfe_image}-tdr"))
    return items


# Load all configuration entries
hooks.Filters.CONFIG_DEFAULTS.add_items(
    [(f"THEMETDR_{key}", value) for key, value in config["defaults"].items()]
)
hooks.Filters.CONFIG_UNIQUE.add_items(
    [(f"THEMETDR_{key}", value) for key, value in config["unique"].items()]
)
hooks.Filters.CONFIG_OVERRIDES.add_items(list(config["overrides"].items()))


#  MFEs that are styled using Themetdr
themetdr_styled_mfes = [
    "learning",
    "learner-dashboard",
    "profile",
    "account",
    "discussions",
]


for mfe in themetdr_styled_mfes:
    hooks.Filters.ENV_PATCHES.add_items(
        [
            (
                f"mfe-dockerfile-post-npm-install-{mfe}",
                """
RUN npm install "@edx/frontend-component-footer@git+https://git@github.com/epfl-cede/frontend-component-footer#sms/indigo"
RUN npm install "@edx/brand@git+https://git@github.com/epfl-cede/brand-cede#sms/sumac-blue.3"

""",
            ),
            (
                f"mfe-env-config-runtime-definitions-{mfe}",
                """
const { default: IndigoFooter } = await import('@edx/frontend-component-footer');
""",
            ),
        ]
    )


hooks.Filters.ENV_PATCHES.add_item(
    (
        "mfe-dockerfile-post-npm-install-authn",
        "RUN npm install '@edx/brand@npm:@edly-io/indigo-brand-openedx@^2.2.2'",
    )
)

# Include js file in lms main.html, main_django.html, and certificate.html


# Apply patches from tutor-themetdr
for path in glob(
    os.path.join(
        str(importlib_resources.files("tutorthemetdr") / "patches"),
        "*",
    )
):
    with open(path, encoding="utf-8") as patch_file:
        hooks.Filters.ENV_PATCHES.add_item((os.path.basename(path), patch_file.read()))


for mfe in themetdr_styled_mfes:
    PLUGIN_SLOTS.add_item(
        (
            mfe,
            "footer_slot",
            """
            {
                op: PLUGIN_OPERATIONS.Hide,
                widgetId: 'default_contents',
            },
            {
                op: PLUGIN_OPERATIONS.Insert,
                widget: {
                    id: 'default_contents',
                    type: DIRECT_PLUGIN,
                    priority: 1,
                    RenderWidget: <IndigoFooter />,
                },
            },
  """,
        ),
    )
