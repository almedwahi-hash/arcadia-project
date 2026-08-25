#!/usr/bin/env python3
"""Round 7: alt-text snippet #24, bulk media alt, cross-link all 7 guides, verify."""
import json
import re
import subprocess
import urllib.parse

COOKIE = "/tmp/wp_work.txt"
BASE = "https://arcadia-tour.com"
USER = "almedwahi@gmail.com"
PWD = "s^r8ium6PzLsEmT8vs"

GUIDE_URLS = [
    ("تكلفة كازاخستان", "/kazakhstan-family-trip-cost-2026/"),
    ("أفضل وقت ألماتي", "/best-time-visit-almaty-2026/"),
    ("تكلفة روسيا", "/russia-family-trip-cost-2026/"),
    ("أفضل وقت موسكو", "/best-time-visit-moscow-2026/"),
    ("تكلفة بولندا", "/poland-family-trip-cost/"),
    ("تكلفة أوزبكستان", "/uzbekistan-family-trip-cost-2026/"),
    ("تكلفة الصين", "/china-family-trip-cost-2026/"),
]

MEDIA_ALT = {
    4306: "\u0625\u0646\u0641\u0648\u062c\u0631\u0627\u0641\u064a\u0643 \u062a\u0643\u0644\u0641\u0629 \u0631\u062d\u0644\u0629 \u0631\u0648\u0633\u064a\u0627 \u0644\u0644\u0639\u0627\u0626\u0644\u0627\u062a 2026 \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627",
    4345: "\u0628\u0631\u0646\u0627\u0645\u062c 7 \u0623\u064a\u0627\u0645 \u0623\u0648\u0632\u0628\u0643\u0633\u062a\u0627\u0646 \u0644\u0644\u0639\u0627\u0626\u0644\u0629 \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627",
    4351: "Uzbekistan 7-day family itinerary infographic \u2014 Arcadia Tours",
    4347: "\u062c\u062f\u0648\u0644 \u0645\u064a\u0632\u0627\u0646\u064a\u0629 \u0631\u062d\u0644\u0629 \u0639\u0627\u0626\u0644\u064a\u0629 \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627 \u0627\u0644\u0633\u064a\u0627\u062d\u064a\u0629",
    4349: "\u0645\u0642\u0627\u0631\u0646\u0629 \u0633\u0627\u0626\u0642 \u0645\u0633\u062a\u0642\u0644 \u0648\u0628\u0627\u0643\u062c \u0633\u064a\u0627\u062d\u064a \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627",
    796: "\u0627\u0644\u0633\u064a\u0627\u062d\u0629 \u0641\u064a \u0631\u0648\u0633\u064a\u0627 \u2014 \u0631\u062d\u0644\u0627\u062a \u0639\u0627\u0626\u0644\u064a\u0629 \u0645\u0639 \u0645\u0631\u0634\u062f \u0639\u0631\u0628\u064a | \u0623\u0631\u0643\u0627\u062f\u064a\u0627",
    791: "\u0631\u062d\u0644\u0627\u062a \u0631\u0648\u0633\u064a\u0627 \u0644\u0644\u0639\u0627\u0626\u0644\u0627\u062a \u0627\u0644\u0639\u0631\u0628\u064a\u0629 \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627 \u0627\u0644\u0633\u064a\u0627\u062d\u064a\u0629",
    792: "\u0627\u0644\u0633\u064a\u0627\u062d\u0629 \u0641\u064a \u0628\u0648\u0644\u0646\u062f\u0627 \u2014 \u0643\u0631\u0627\u0643\u0648\u0641 \u0648\u0648\u0627\u0631\u0633\u0648 | \u0623\u0631\u0643\u0627\u062f\u064a\u0627",
    793: "\u0627\u0644\u0633\u064a\u0627\u062d\u0629 \u0641\u064a \u0623\u0648\u0632\u0628\u0643\u0633\u062a\u0627\u0646 \u2014 \u0633\u0645\u0631\u0642\u0646\u062f \u0648\u0628\u062e\u0627\u0631\u0629 | \u0623\u0631\u0643\u0627\u062f\u064a\u0627",
    797: "\u0631\u062d\u0644\u0629 \u0639\u0627\u0626\u0644\u064a\u0629 \u0625\u0644\u0649 \u0628\u0648\u0644\u0646\u062f\u0627 \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627 \u0627\u0644\u0633\u064a\u0627\u062d\u064a\u0629",
    798: "\u0631\u062d\u0644\u0629 \u0639\u0627\u0626\u0644\u064a\u0629 \u0625\u0644\u0649 \u0623\u0648\u0632\u0628\u0643\u0633\u062a\u0627\u0646 \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627 \u0627\u0644\u0633\u064a\u0627\u062d\u064a\u0629",
    779: "\u0627\u0644\u0633\u064a\u0627\u062d\u0629 \u0641\u064a \u0643\u0631\u0627\u0643\u0648\u0641 \u0628\u0648\u0644\u0646\u062f\u0627 \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627",
    782: "\u0628\u0631\u0627\u0645\u062c \u0623\u0648\u0632\u0628\u0643\u0633\u062a\u0627\u0646 \u0627\u0644\u0633\u064a\u0627\u062d\u064a \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627",
    783: "\u0628\u0631\u0627\u0645\u062c \u0631\u0648\u0633\u064a\u0627 \u0627\u0644\u0633\u064a\u0627\u062d\u064a \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627",
    1862: "\u0628\u0631\u0646\u0627\u0645\u062c \u0645\u0648\u0633\u0643\u0648 \u0648\u0633\u0627\u0646\u062a \u0628\u062a\u0631\u0628\u0648\u0631\u063a \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627",
    1863: "\u0628\u0631\u0646\u0627\u0645\u062c \u0631\u0648\u0633\u064a\u0627 8 \u0623\u064a\u0627\u0645 \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627 \u0627\u0644\u0633\u064a\u0627\u062d\u064a\u0629",
    1864: "\u0628\u0631\u0646\u0627\u0645\u062c \u0631\u0648\u0633\u064a\u0627 7 \u0623\u064a\u0627\u0645 \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627",
    1870: "\u0645\u0631\u0628\u0639 \u0627\u0644\u0643\u0631\u0645\u0644\u064a\u0646 \u0641\u064a \u0645\u0648\u0633\u0643\u0648 \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627",
    1903: "\u0645\u0648\u0633\u0643\u0648 \u0627\u0644\u0645\u0648\u0633\u0645 \u0627\u0644\u0645\u0645\u0637\u0631 \u2014 \u0631\u062d\u0644\u0627\u062a \u0623\u0631\u0643\u0627\u062f\u064a\u0627",
    4573: "\u0623\u0631\u0643\u0627\u062f\u064a\u0627 \u0627\u0644\u0633\u064a\u0627\u062d\u064a\u0629 \u2014 \u0631\u062d\u0644\u0627\u062a \u0639\u0627\u0626\u0644\u064a\u0629 \u0625\u0644\u0649 \u0643\u0627\u0632\u0627\u062e\u0633\u062a\u0627\u0646 \u0648\u0631\u0648\u0633\u064a\u0627 \u0648\u0628\u0648\u0644\u0646\u062f\u0627",
    4576: "\u0623\u0631\u0643\u0627\u062f\u064a\u0627 \u0627\u0644\u0633\u064a\u0627\u062d\u064a\u0629 \u2014 \u062f\u0644\u0627\u0626\u0644 \u0627\u0644\u0623\u0633\u0639\u0627\u0631 \u0648\u0627\u0644\u0645\u0648\u0627\u0633\u0645 2026",
}


def curl(path, method="GET", data=None, cookie=True, extra_headers=None):
    cmd = ["curl", "-s", "-L", "-X", method]
    if cookie:
        cmd += ["-b", COOKIE, "-c", COOKIE]
    cmd.append(path if path.startswith("http") else f"{BASE}{path}")
    if extra_headers:
        for h in extra_headers:
            cmd += ["-H", h]
    if data is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(data, ensure_ascii=False)]
    return subprocess.check_output(cmd, text=True)


def login():
    page = subprocess.check_output(
        ["curl", "-s", "-c", COOKIE, "-b", COOKIE, f"{BASE}/wp-login.php"], text=True
    )
    fields = {
        "log": USER, "pwd": PWD, "wp-submit": "Log In",
        "redirect_to": f"{BASE}/wp-admin/", "testcookie": "1",
    }
    m = re.search(r"(\d+)\s*\+\s*(\d+)", page)
    if m:
        ans = int(m.group(1)) + int(m.group(2))
        for nm in re.findall(r'name="([^"]+)"', page):
            if nm not in ("log", "pwd", "wp-submit", "redirect_to", "testcookie", "rememberme", "_wpnonce", "_wp_http_referer"):
                fields[nm] = str(ans)
                break
    subprocess.check_output(
        ["curl", "-s", "-b", COOKIE, "-c", COOKIE, "-L", "-X", "POST",
         f"{BASE}/wp-login.php", "--data", urllib.parse.urlencode(fields)], text=True
    )
    admin = subprocess.check_output(["curl", "-s", "-b", COOKIE, f"{BASE}/wp-admin/"], text=True)
    if "wp-login.php" in admin[:1000] and "dashboard" not in admin.lower():
        raise RuntimeError("WP login failed")
    print("\u2713 Logged in")


def snippet_nonce():
    html = curl(f"{BASE}/wp-admin/admin.php?page=edit-snippet&id=21")
    return re.search(r'wpApiSettings\s*=\s*\{[^}]*"nonce"\s*:\s*"([^"]+)"', html).group(1)


def api_nonce():
    admin = curl(f"{BASE}/wp-admin/")
    return re.search(r'wpApiSettings\s*=\s*\{[^}]*"nonce"\s*:\s*"([^"]+)"', admin).group(1)


def snippets_api(path, method="GET", data=None, n=None):
    return curl(f"{BASE}{path}", method, data, extra_headers=[f"X-WP-Nonce: {n}"])


def media_api(path, method="GET", data=None, n=None):
    return curl(f"{BASE}{path}", method, data, extra_headers=[f"X-WP-Nonce: {n}"])


def snippet24_code():
    id_map_lines = []
    for mid, alt in MEDIA_ALT.items():
        id_map_lines.append(f"\t\t{mid} => '{alt}',")
    id_map = "\n".join(id_map_lines)
    return f'''/**
 * Arcadia Alt Text SEO Engine (Aug 2026).
 * Fills missing alt on attachment images + content imgs via filename/slug heuristics.
 */
if ( ! defined( 'ABSPATH' ) ) {{
\treturn;
}}

function arcadia_alt_id_map() {{
\treturn array(
{id_map}
\t);
}}

function arcadia_alt_from_filename( $filename ) {{
\t$base = strtolower( pathinfo( $filename, PATHINFO_FILENAME ) );
\t$rules = array(
\t\t'russia'      => '\u0627\u0644\u0633\u064a\u0627\u062d\u0629 \u0641\u064a \u0631\u0648\u0633\u064a\u0627 \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627 \u0627\u0644\u0633\u064a\u0627\u062d\u064a\u0629',
\t\t'poland'      => '\u0627\u0644\u0633\u064a\u0627\u062d\u0629 \u0641\u064a \u0628\u0648\u0644\u0646\u062f\u0627 \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627 \u0627\u0644\u0633\u064a\u0627\u062d\u064a\u0629',
\t\t'uzbek'       => '\u0627\u0644\u0633\u064a\u0627\u062d\u0629 \u0641\u064a \u0623\u0648\u0632\u0628\u0643\u0633\u062a\u0627\u0646 \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627 \u0627\u0644\u0633\u064a\u0627\u062d\u064a\u0629',
\t\t'kazakh'      => '\u0627\u0644\u0633\u064a\u0627\u062d\u0629 \u0641\u064a \u0643\u0627\u0632\u0627\u062e\u0633\u062a\u0627\u0646 \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627 \u0627\u0644\u0633\u064a\u0627\u062d\u064a\u0629',
\t\t'almaty'      => '\u0623\u0641\u0636\u0644 \u0627\u0644\u0623\u0648\u0642\u0627\u062a \u0644\u0632\u064a\u0627\u0631\u0629 \u0623\u0644\u0645\u0627\u062a\u064a \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627',
\t\t'moscow'      => '\u062f\u0644\u064a\u0644 \u0645\u0648\u0633\u0643\u0648 \u0648\u0623\u0641\u0636\u0644 \u0648\u0642\u062a \u0644\u0644\u0632\u064a\u0627\u0631\u0629 \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627',
\t\t'china'       => '\u0627\u0644\u0633\u064a\u0627\u062d\u0629 \u0641\u064a \u0627\u0644\u0635\u064a\u0646 \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627 \u0627\u0644\u0633\u064a\u0627\u062d\u064a\u0629',
\t\t'family'      => '\u0631\u062d\u0644\u0629 \u0639\u0627\u0626\u0644\u064a\u0629 \u0645\u0639 \u0623\u0631\u0643\u0627\u062f\u064a\u0627 \u0627\u0644\u0633\u064a\u0627\u062d\u064a\u0629',
\t\t'infographic' => '\u0625\u0646\u0641\u0648\u062c\u0631\u0627\u0641\u064a\u0643 \u0633\u064a\u0627\u062d\u064a \u2014 \u0623\u0631\u0643\u0627\u062f\u064a\u0627',
\t\t'arcadia'     => '\u0623\u0631\u0643\u0627\u062f\u064a\u0627 \u0627\u0644\u0633\u064a\u0627\u062d\u064a\u0629 \u2014 \u0631\u062d\u0644\u0627\u062a \u0639\u0627\u0626\u0644\u064a\u0629',
\t);
\tforeach ( $rules as $needle => $alt ) {{
\t\tif ( false !== strpos( $base, $needle ) ) {{
\t\t\treturn $alt;
\t\t}}
\t}}
\treturn '';
}}

function arcadia_alt_resolve( $attachment_id, $src = '' ) {{
\t$map = arcadia_alt_id_map();
\tif ( $attachment_id && isset( $map[ (int) $attachment_id ] ) ) {{
\t\treturn $map[ (int) $attachment_id ];
\t}}
\tif ( $attachment_id ) {{
\t\t$stored = get_post_meta( (int) $attachment_id, '_wp_attachment_image_alt', true );
\t\tif ( is_string( $stored ) && trim( $stored ) !== '' ) {{
\t\t\treturn trim( $stored );
\t\t}}
\t}}
\tif ( $src ) {{
\t\t$filename = wp_basename( parse_url( $src, PHP_URL_PATH ) );
\t\t$guess    = arcadia_alt_from_filename( $filename );
\t\tif ( $guess ) {{
\t\t\treturn $guess;
\t\t}}
\t}}
\treturn '';
}}

add_filter(
\t'wp_get_attachment_image_attributes',
\tfunction ( $attr, $attachment ) {{
\t\tif ( ! empty( $attr['alt'] ) ) {{
\t\t\treturn $attr;
\t\t}}
\t\t$id  = is_object( $attachment ) ? (int) $attachment->ID : (int) $attachment;
\t\t$alt = arcadia_alt_resolve( $id, isset( $attr['src'] ) ? $attr['src'] : '' );
\t\tif ( $alt ) {{
\t\t\t$attr['alt'] = $alt;
\t\t}}
\t\treturn $attr;
\t}},
\t20,
\t2
);

add_filter(
\t'the_content',
\tfunction ( $content ) {{
\t\tif ( is_admin() || false === strpos( $content, '<img' ) ) {{
\t\t\treturn $content;
\t\t}}
\t\treturn preg_replace_callback(
\t\t\t'/<img([^>]*?)>/i',
\t\t\tfunction ( $m ) {{
\t\t\t\t$tag = $m[0];
\t\t\t\tif ( preg_match( '/\\balt\\s*=\\s*([\\\'"]).*?\\1/i', $tag ) ) {{
\t\t\t\t\treturn $tag;
\t\t\t\t}}
\t\t\t\tif ( preg_match( '/data:image\\/svg\\+xml/i', $tag ) ) {{
\t\t\t\t\treturn $tag;
\t\t\t\t}}
\t\t\t\t$src = '';
\t\t\t\tif ( preg_match( '/\\bsrc\\s*=\\s*([\\\'"])(.*?)\\1/i', $tag, $sm ) ) {{
\t\t\t\t\t$src = $sm[2];
\t\t\t\t}}
\t\t\t\t$attachment_id = 0;
\t\t\t\tif ( preg_match( '/\\bclass\\s*=\\s*([\\\'"])(.*?)\\1/i', $tag, $cm ) && preg_match( '/wp-image-(\\d+)/', $cm[2], $im ) ) {{
\t\t\t\t\t$attachment_id = (int) $im[1];
\t\t\t\t}}
\t\t\t\t$alt = arcadia_alt_resolve( $attachment_id, $src );
\t\t\t\tif ( ! $alt ) {{
\t\t\t\t\treturn $tag;
\t\t\t\t}}
\t\t\t\treturn str_replace( '<img', '<img alt="' . esc_attr( $alt ) . '"', $tag );
\t\t\t}},
\t\t\t$content
\t\t);
\t}},
\t25
);
'''


def create_or_update_snippet24(n):
    snippets = json.loads(snippets_api("/wp-json/code-snippets/v1/snippets", n=n))
    existing = next((s for s in snippets if "Alt Text SEO" in s.get("name", "")), None)
    payload = {
        "name": "Arcadia Alt Text SEO Engine 2026-08-25",
        "desc": "Auto alt text for SEO images + filename heuristics",
        "code": snippet24_code(),
        "scope": "global",
        "active": True,
        "priority": 10,
    }
    if existing:
        resp = snippets_api(f"/wp-json/code-snippets/v1/snippets/{existing['id']}", "PUT", payload, n)
        print(f"\u2713 Updated snippet #{existing['id']} Alt Text SEO")
    else:
        resp = snippets_api("/wp-json/code-snippets/v1/snippets", "POST", payload, n)
        data = json.loads(resp)
        print(f"\u2713 Created snippet #{data.get('id')} Alt Text SEO")


def update_snippet22_guides(n):
    s22 = json.loads(snippets_api("/wp-json/code-snippets/v1/snippets/22", n=n))
    code = s22["code"]
    if "arcadia-all-guides-2026" in code:
        print("\u2713 Snippet 22 already has all-guides block")
        return
    guides_php = "\t\t\t'\\u062a\\u0643\\u0644\\u0641\\u0629 \\u0643\\u0627\\u0632\\u0627\\u062e\\u0633\\u062a\\u0627\\u0646' => '/kazakhstan-family-trip-cost-2026/',\n"
    for label, url in GUIDE_URLS[1:]:
        guides_php += f"\t\t\t'{label}' => '{url}',\n"
    block = f'''
function arcadia_blog_seo_all_guides() {{
\treturn array(
{guides_php}\t);
}}
'''
    code = code.replace(
        "function arcadia_blog_seo_current_config()",
        block + "\nfunction arcadia_blog_seo_current_config()",
    )
    insert = """
\t\t$all_guides = arcadia_blog_seo_all_guides();
\t\t$guide_lis  = '';
\t\tforeach ( $all_guides as $label => $url ) {
\t\t\t$guide_lis .= '<li><a href="' . esc_url( home_url( $url ) ) . '">' . esc_html( $label ) . '</a></li>';
\t\t}
\t\techo '<h3 style="font-size:1rem;margin:0 0 .5rem">دلائل الأسعار والمواسم 2026</h3>';
\t\techo '<ul class="arcadia-all-guides-2026" style="margin:0 0 1rem;padding-right:1.25rem">' . $guide_lis . '</ul>';
"""
    code = code.replace(
        "\t\techo '<h3 style=\"font-size:1rem;margin:0 0 .5rem\">وجهاتنا النشطة</h3>';",
        insert + "\t\techo '<h3 style=\"font-size:1rem;margin:0 0 .5rem\">وجهاتنا النشطة</h3>';",
    )
    snippets_api("/wp-json/code-snippets/v1/snippets/22", "PUT", {"code": code, "active": True}, n)
    print("\u2713 Snippet 22 updated with all 7 guides cross-link")


def update_snippet23_china(n):
    s23 = json.loads(snippets_api("/wp-json/code-snippets/v1/snippets/23", n=n))
    code = s23["code"]
    if "china-family-trip-cost-2026" in code:
        print("\u2713 Snippet 23 already has China guide")
        return
    code = code.replace(
        "'\u062a\u0643\u0644\u0641\u0629 \u0623\u0648\u0632\u0628\u0643\u0633\u062a\u0627\u0646'           => '/uzbekistan-family-trip-cost-2026/',",
        "'\u062a\u0643\u0644\u0641\u0629 \u0623\u0648\u0632\u0628\u0643\u0633\u062a\u0627\u0646'           => '/uzbekistan-family-trip-cost-2026/',\n\t\t\t'\u062a\u0643\u0644\u0641\u0629 \u0627\u0644\u0635\u064a\u0646 \u0644\u0644\u0639\u0627\u0626\u0644\u0627\u062a'     => '/china-family-trip-cost-2026/',",
    )
    snippets_api("/wp-json/code-snippets/v1/snippets/23", "PUT", {"code": code, "active": True}, n)
    print("\u2713 Snippet 23 updated with China guide link")


def bulk_media_alt(n):
    updated = 0
    for mid, alt in MEDIA_ALT.items():
        resp = media_api(f"/wp-json/wp/v2/media/{mid}", "POST", {"alt_text": alt}, n)
        try:
            data = json.loads(resp)
            if data.get("id"):
                updated += 1
                print(f"  \u2713 media {mid}: {alt[:50]}...")
        except json.JSONDecodeError:
            print(f"  \u2717 media {mid}: {resp[:80]}")
    print(f"\u2713 Bulk alt updated: {updated}/{len(MEDIA_ALT)}")


def purge_cache():
    subprocess.check_output([
        "curl", "-s", "-b", COOKIE, "-L",
        f"{BASE}/wp-admin/admin.php?page=litespeed-toolbox&LSCWP_CTRL=purge&litespeed-action=purge_all",
    ], text=True)
    print("\u2713 Cache purged")


def verify():
    urls = [
        "https://arcadia-tour.com/kazakhstan-family-trip-cost-2026/",
        "https://arcadia-tour.com/china-family-trip-cost-2026/",
        "https://arcadia-tour.com/%D8%A7%D9%84%D8%B3%D9%8A%D8%A7%D8%AD%D8%A9-%D9%81%D9%8A-%D8%B1%D9%88%D8%B3%D9%8A%D8%A7/",
    ]
    for url in urls:
        html = subprocess.check_output(
            ["curl", "-sL", url, "-H", "Cache-Control: no-cache"], text=True
        )
        guides = "arcadia-all-guides-2026" in html
        hub = "arcadia-blog-seo-hub" in html or "arcadia-home-seo-hub" in html
        imgs_no_alt = len(re.findall(r'<img(?![^>]*\balt\s*=)[^>]*>', html, re.I))
        print(f"\n{url[:65]}")
        print(f"  guides block: {guides}  hub: {hub}  imgs w/o alt: {imgs_no_alt}")

    # check media alt via REST
    n = api_nonce()
    m = json.loads(media_api("/wp-json/wp/v2/media/4306", n=n))
    print(f"\nmedia 4306 alt: {m.get('alt_text','')[:60]}")


def main():
    login()
    sn = snippet_nonce()
    an = api_nonce()
    create_or_update_snippet24(sn)
    bulk_media_alt(an)
    update_snippet22_guides(sn)
    update_snippet23_china(sn)
    purge_cache()
    verify()


if __name__ == "__main__":
    main()
