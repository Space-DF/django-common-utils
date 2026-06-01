from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError


def _get_contrast_color(color):
    value = (color or "#FFFFFF").strip()
    if not value.startswith("#"):
        value = f"#{value}"

    if len(value) == 4:
        value = "#" + "".join(char * 2 for char in value[1:])

    if len(value) != 7:
        value = "#FFFFFF"

    try:
        red = int(value[1:3], 16)
        green = int(value[3:5], 16)
        blue = int(value[5:7], 16)
    except ValueError:
        red, green, blue = 255, 255, 255

    brightness = (red * 299 + green * 587 + blue * 114) / 1000
    return "#000000" if brightness >= 128 else "#FFFFFF"


def _get_value(source, key, default=None):
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _get_theme_colors(source):
    return _get_value(source, "theme_colors", {}) or {}


def _get_visibility_flags(source):
    return _get_value(source, "metadata", {}) or {}


def _get_social_links(source):
    return _get_value(source, "social_links", {}) or {}


def _prefers_light_logo(background_color):
    return _get_contrast_color(background_color) == "#000000"


def _pick_brand_logo(prefer_light_logo, logo_light_url, logo_dark_url):
    if prefer_light_logo:
        return logo_light_url or logo_dark_url
    return logo_dark_url or logo_light_url


def get_email_context(email_context_data, custom_email):
    custom_email = custom_email or {}
    theme_colors = _get_theme_colors(custom_email)
    visibility_flags = _get_visibility_flags(custom_email)
    social_links = _get_social_links(custom_email)
    background_color = theme_colors.get("background_color") or "#FFFFFF"
    primary_color = theme_colors.get("primary_color") or "#1c1c28"
    contrast_primary_color = _get_contrast_color(primary_color)
    logo_light_url = _get_value(custom_email, "brand_logo_light") or ""
    logo_dark_url = _get_value(custom_email, "brand_logo_dark") or ""

    active_brand_header_logo = _pick_brand_logo(
        _prefers_light_logo(background_color),
        logo_light_url,
        logo_dark_url,
    )
    active_brand_footer_logo = _pick_brand_logo(
        _prefers_light_logo(primary_color),
        logo_light_url,
        logo_dark_url,
    )

    email_context_data.update(
        {
            "brand_name": _get_value(custom_email, "brand_name") or "SpaceDF",
            "show_logo": _get_value(custom_email, "show_logo", True),
            "background_image_url": _get_value(custom_email, "url_background_image")
            or "",
            "sender_from": (_get_value(custom_email, "sender_name") or ""),
            "brand_logo_dark": logo_dark_url,
            "brand_logo_light": logo_light_url,
            "active_brand_header_logo": active_brand_header_logo,
            "active_brand_footer_logo": active_brand_footer_logo,
            "sender_email": (
                _get_value(custom_email, "sender_email")
                or email_context_data.get("sender_email", "support@spacedf.com")
            ),
            "email_footer": (_get_value(custom_email, "footer_text") or ""),
            "header_image_url": _get_value(custom_email, "url_header_image") or "",
            "linkedin_url": social_links.get(
                "linkedin_url",
                "",
            ),
            "facebook_url": social_links.get("facebook_url"),
            "instagram_url": social_links.get("instagram_url"),
            "tiktok_url": social_links.get("tiktok_url"),
            "show_facebook": visibility_flags.get(
                "show_facebook",
                True,
            ),
            "show_linkedin": visibility_flags.get(
                "show_linkedin",
                True,
            ),
            "show_instagram": visibility_flags.get(
                "show_instagram",
                True,
            ),
            "show_tiktok": visibility_flags.get(
                "show_tiktok",
                True,
            ),
            "primary_color": primary_color,
            "background_color": background_color,
            "contrast_primary_color": contrast_primary_color,
        }
    )
    return email_context_data


def render_email_format(template, data):
    try:
        html_message = render_to_string(template, data)
        return html_message
    except Exception as e:
        raise ValidationError({"error": f"Error: {e}"})
