# WD Display branding notes

Rebrand and restyle pass for the Android receiver. Behavior, protocol, service,
permissions and lifecycle were not changed; only labels, presentation and
artwork.

## Name

User-visible product name is **WD Display**. The Android `app_name` string was
already `WD Display`, but the in-app header still rendered "Wormhole Display";
that heading and the device-name hint now read WD Display. Internal class,
package and JNI symbol names remain `org.pocketairdisplay.receiver` and
`WormholeServer` etc., because those are install and native-ABI identity, not
branding.

## Mark

Two mirrored right-angle strokes forming an italic W, constructed as a single
closed path (`design/art/wd-mark.svg`), no text, no third-party or Apple
artwork. Rendered as a soft glass object: a light-to-mid vertical gradient, a
soft inner shade on the lower right of each stroke, and a thin specular
highlight along the upper edges, on a dark neutral rounded tile. The mark is
verified legible at the shipped 48dp density and stays inside the 66dp safe
square of the 108dp adaptive-icon canvas, so any launcher mask crops tile only.

## Shipped assets

| Asset | Path |
|---|---|
| Master mark (geometry) | `design/art/wd-mark.svg` |
| Generator (deterministic) | `design/art/generate_wd_art.py` |
| Inspector used for checks | `design/art/inspect_png.py` |
| Adaptive icon | `app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml` |
| Adaptive foreground / background / monochrome | `app/src/main/res/drawable-xxxhdpi/ic_launcher_{foreground,background,monochrome}.png` |
| Legacy launcher icons | `app/src/main/res/mipmap-{mdpi,hdpi,xhdpi,xxhdpi,xxxhdpi}/ic_launcher.png` |
| TV banner | `app/src/main/res/drawable/tv_banner.png`, `app/src/main/res/drawable-xhdpi/tv_banner.png` |
| Vector monochrome | `app/src/main/res/drawable/ic_wd_monochrome.xml` |

The generator is not part of the published source bundle (the bundle allowlist
covers `app/src/main`, `app/src/test`, `app/src/androidTest`, `scripts`,
`tests`); the rendered PNGs that actually ship are included through
`app/src/main/res`. Recorded here so the artwork stays reproducible.

## Design tokens

`app/src/main/java/org/pocketairdisplay/receiver/WdTheme.kt` is the single place
color and type values live. Everything in the UI resolves tokens from it; no
raw `Color(0x...)` literal remains in `MainActivity.kt`.

- Colors: background, groupedSurface, elevatedSurface, hairline,
  separatorStrong, labelPrimary/Secondary/Tertiary, accent, accentMuted,
  accentBorder, accentBright, highlightEdge, shadow, success, warning,
  destructive, focusBackground, warningSurface, scrim. Dark and light sets are
  resolved per appearance with `isSystemInDarkTheme()`.
- Spacing: 4/8/12/16/20/24dp. Radii: 10dp grouped, 12dp large, 8dp small,
  pill. Type ramp on the platform font: 34sp large title (slightly negative
  tracking), 20sp title3 semibold, 17sp body, 15sp subheadline, 13sp footnote,
  12sp caption, 13sp tracked section header.
- Primitives: `WdGroupedCard`, `WdRow`, `WdSectionHeader`, `WdInfoRow`,
  `WdMarkTile`, `WdStatusHero`, plus `WdAppTheme` which also maps the tokens
  onto the Material3 scheme for any remaining Material component.

Apple-system grammar applied: grouped inset cards with hairline separators,
leading-title rows with trailing controls, a pill segmented control for screen
orientation, hierarchical label colors, and restrained translucency (a thin
highlight edge and soft shadow on layered surfaces) rather than gradients. No
emoji, no blur wash. Information architecture is unchanged: same sections, rows,
controls and copy, in the same order.

## Verification performed

- Icons and banner rendered by the generator; inspected visually at 48dp and at
  full density for legibility, clipping and alpha.
- `:app:compileDebugKotlin` compiles; full `scripts/build.sh` host gate passes
  (JVM 75 tests, native and production-core suites, native audit regressions,
  alignment and signature gates) and publishes a coherent release.
- On the authorized Galaxy A55: install of the rebuilt application and test
  APKs succeeded, the device startup validator passed cold Activity and
  service-first checks, and the accessibility hierarchy confirms the new UI
  renders (title WD Display, orientation segmented control, grouped setting
  rows, recent connections).
- Not verified: on-device screenshots are impossible for this app because the
  video surface sets FLAG_SECURE, so visual confirmation comes from the
  generated renders plus the rendered text hierarchy, not a captured screen.
