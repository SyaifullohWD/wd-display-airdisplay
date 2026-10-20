package org.pocketairdisplay.receiver

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ColorScheme
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.ReadOnlyComposable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * WD design tokens: an explicit, tiny token layer modelled on Apple's system
 * visual grammar (grouped inset surfaces, hairline separators, restrained
 * translucency, a type ramp built on the platform font).
 *
 * Every colour used by the restyled UI lives here; call sites must not carry hex.
 */
@Immutable
data class WdColors(
    /** Page background behind grouped content (system grouped background). */
    val background: Color,
    /** Inset grouped card fill. */
    val groupedSurface: Color,
    /** Raised/translucent surface layer used for chips, tiles, floating rows. */
    val elevatedSurface: Color,
    /** Hairline separator / card border. */
    val hairline: Color,
    /** Stronger separator for the light appearance where 1px must stay visible. */
    val separatorStrong: Color,
    /** Primary label (titles, values). */
    val labelPrimary: Color,
    /** Secondary label (subtitles, row labels). */
    val labelSecondary: Color,
    /** Tertiary label (captions, disabled, low-emphasis meta). */
    val labelTertiary: Color,
    /** Interaction/selection accent. */
    val accent: Color,
    /** Tinted accent fill used for status/selection backgrounds. */
    val accentMuted: Color,
    /** Tinted accent border for status/selection outlines. */
    val accentBorder: Color,
    /** Soft highlight edge painted on top of cards (thin, low alpha). */
    val highlightEdge: Color,
    /** Soft shadow colour for layered depth. */
    val shadow: Color,
    val success: Color,
    val warning: Color,
    val destructive: Color,
    /** Brighter accent for focus/press emphasis on the accent itself. */
    val accentBright: Color,
    /** Background wash for a focused control. */
    val focusBackground: Color,
    /** Background wash behind warning copy. */
    val warningSurface: Color,
    /** Dimming layer behind overlays and dialogs. */
    val scrim: Color,
    /** Track of an "on" switch. */
    val switchOn: Color,
    /** Track of an "off" switch. */
    val switchOffTrack: Color,
    /** Switch thumb. */
    val switchThumb: Color
)

/**
 * Dark appearance: iOS system colors in dark. Pure black page, gray grouped
 * cards, system blue tint, system green switches.
 */
private val WdDarkColors = WdColors(
    background = Color(0xFF000000),
    groupedSurface = Color(0xFF1C1C1E),
    elevatedSurface = Color(0xFF2C2C2E),
    hairline = Color(0x5B545458),
    separatorStrong = Color(0x8E545458),
    labelPrimary = Color(0xFFFFFFFF),
    labelSecondary = Color(0x99EBEBF5),
    labelTertiary = Color(0x4DEBEBF5),
    accent = Color(0xFF0A84FF),
    accentMuted = Color(0xFF10243A),
    accentBorder = Color(0xFF1F4B7A),
    highlightEdge = Color(0x1FFFFFFF),
    shadow = Color(0x99000000),
    success = Color(0xFF30D158),
    warning = Color(0xFFFF9F0A),
    destructive = Color(0xFFFF453A),
    accentBright = Color(0xFF409CFF),
    focusBackground = Color(0xFF14263C),
    warningSurface = Color(0xFF2A1F0A),
    scrim = Color(0xCC000000),
    switchOn = Color(0xFF34C759),
    switchOffTrack = Color(0xFF39393D),
    switchThumb = Color(0xFFFFFFFF)
)

/** Light appearance: iOS system colors in light. */
private val WdLightColors = WdColors(
    background = Color(0xFFF2F2F7),
    groupedSurface = Color(0xFFFFFFFF),
    elevatedSurface = Color(0xFFFFFFFF),
    hairline = Color(0x4A3C3C43),
    separatorStrong = Color(0x663C3C43),
    labelPrimary = Color(0xFF000000),
    labelSecondary = Color(0x993C3C43),
    labelTertiary = Color(0x4D3C3C43),
    accent = Color(0xFF007AFF),
    accentMuted = Color(0xFFE7F0FE),
    accentBorder = Color(0xFFB3D4FF),
    highlightEdge = Color(0x14FFFFFF),
    shadow = Color(0x1A000000),
    success = Color(0xFF34C759),
    warning = Color(0xFFFF9500),
    destructive = Color(0xFFFF3B30),
    accentBright = Color(0xFF0A84FF),
    focusBackground = Color(0xFFE8F1FF),
    warningSurface = Color(0xFFFFF4E5),
    scrim = Color(0x99000000),
    switchOn = Color(0xFF34C759),
    switchOffTrack = Color(0xFFE9E9EA),
    switchThumb = Color(0xFFFFFFFF)
)

/** Spacing scale (dp). */
object WdSpacing {
    val xs: Dp = 4.dp
    val sm: Dp = 8.dp
    val md: Dp = 12.dp
    val lg: Dp = 16.dp
    val xl: Dp = 20.dp
    val xxl: Dp = 24.dp
}

/** Corner radii (dp). */
object WdRadius {
    /** Grouped/inset card. */
    val grouped: Dp = 10.dp
    /** Large card. */
    val large: Dp = 12.dp
    /** Small inline control. */
    val small: Dp = 8.dp
    /** Pill / capsule. */
    val pill: Dp = 999.dp
}

/** Type ramp on the platform font, Apple-like sizes and tracking. */
object WdType {
    val largeTitle = TextStyle(
        fontFamily = FontFamily.Default,
        fontSize = 34.sp,
        fontWeight = FontWeight.Bold,
        letterSpacing = (-0.4).sp
    )
    val title3 = TextStyle(
        fontFamily = FontFamily.Default,
        fontSize = 20.sp,
        fontWeight = FontWeight.SemiBold,
        letterSpacing = (-0.2).sp
    )
    val body = TextStyle(
        fontFamily = FontFamily.Default,
        fontSize = 17.sp,
        fontWeight = FontWeight.Normal,
        letterSpacing = (-0.1).sp
    )
    val subheadline = TextStyle(
        fontFamily = FontFamily.Default,
        fontSize = 15.sp,
        fontWeight = FontWeight.Normal,
        letterSpacing = 0.sp
    )
    val footnote = TextStyle(
        fontFamily = FontFamily.Default,
        fontSize = 13.sp,
        fontWeight = FontWeight.Normal,
        letterSpacing = 0.sp
    )
    val caption = TextStyle(
        fontFamily = FontFamily.Default,
        fontSize = 12.sp,
        fontWeight = FontWeight.Normal,
        letterSpacing = 0.sp
    )
    /** Uppercase-ish grouped section header. */
    val sectionHeader = TextStyle(
        fontFamily = FontFamily.Default,
        fontSize = 13.sp,
        fontWeight = FontWeight.SemiBold,
        letterSpacing = 0.6.sp
    )
}

/** Minimum touch height for an interactive row. */
val WdMinTouchHeight: Dp = 48.dp

val LocalWdColors = staticCompositionLocalOf { WdDarkColors }

object WdTheme {
    val colors: WdColors
        @Composable @ReadOnlyComposable get() = LocalWdColors.current
}

/** Resolves the token set for the current system appearance. */
@Composable
fun rememberWdColors(isDark: Boolean = isSystemInDarkTheme()): WdColors =
    if (isDark) WdDarkColors else WdLightColors

/** Wraps content in the resolved token set. */
@Composable
fun WdTheme(
    isDark: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    CompositionLocalProvider(LocalWdColors provides rememberWdColors(isDark), content = content)
}

// ---------------------------------------------------------------------------
// Primitives
// ---------------------------------------------------------------------------

/**
 * Inset grouped card: grouped surface fill, hairline border in the light
 * appearance, and a soft shadow plus a hairline highlight edge in the dark one.
 * No gradients, no blur — depth comes from layering and one thin highlight.
 */
@Composable
fun WdGroupedCard(
    modifier: Modifier = Modifier,
    isDark: Boolean = isSystemInDarkTheme(),
    shape: RoundedCornerShape = RoundedCornerShape(WdRadius.large),
    contentPadding: Dp = WdSpacing.lg,
    content: @Composable ColumnScope.() -> Unit
) {
    val colors = WdTheme.colors
    Box(
        modifier = modifier
            .clip(shape)
            .background(colors.groupedSurface)
            .then(
                if (isDark) {
                    Modifier.border(0.5.dp, colors.highlightEdge, shape)
                } else {
                    Modifier.border(0.5.dp, colors.hairline, shape)
                }
            )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(contentPadding),
            content = content
        )
    }
}

/** Uppercase-ish grouped section header drawn from the secondary label token. */
@Composable
fun WdSectionHeader(
    text: String,
    modifier: Modifier = Modifier
) {
    Text(
        text = text.uppercase(),
        modifier = modifier,
        style = WdType.sectionHeader,
        color = WdTheme.colors.labelSecondary,
        maxLines = 1,
        overflow = TextOverflow.Ellipsis
    )
}

/**
 * Grouped row: leading title (with optional subtitle) and an optional trailing
 * slot. Hairline divider is drawn at the bottom unless this is the last row.
 * Always keeps at least [minHeight] so it stays a comfortable touch target.
 */
@Composable
fun WdRow(
    title: String,
    modifier: Modifier = Modifier,
    subtitle: String? = null,
    titleStyle: TextStyle = WdType.body,
    subtitleStyle: TextStyle = WdType.footnote,
    minHeight: Dp = WdMinTouchHeight,
    showDivider: Boolean = true,
    dividerInset: Dp = WdSpacing.lg,
    trailing: (@Composable () -> Unit)? = null
) {
    val colors = WdTheme.colors
    Column(modifier = modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .defaultMinSize(minHeight = minHeight)
                .padding(vertical = WdSpacing.xs),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title,
                    style = titleStyle,
                    color = colors.labelPrimary,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                if (subtitle != null) {
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = subtitle,
                        style = subtitleStyle,
                        color = colors.labelSecondary,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }
            if (trailing != null) {
                Spacer(modifier = Modifier.width(WdSpacing.md))
                trailing()
            }
        }
        if (showDivider) {
            HorizontalDivider(
                thickness = 0.5.dp,
                color = colors.hairline,
                modifier = Modifier.padding(start = dividerInset)
            )
        }
    }
}

/** Label/value row used by the connection info block. */
@Composable
fun WdInfoRow(
    label: String,
    value: String,
    modifier: Modifier = Modifier,
    labelStyle: TextStyle = WdType.footnote,
    valueStyle: TextStyle = WdType.footnote
) {
    val colors = WdTheme.colors
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            style = labelStyle,
            color = colors.labelSecondary,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis
        )
        Spacer(modifier = Modifier.width(WdSpacing.sm))
        Text(
            text = value,
            style = valueStyle,
            fontWeight = FontWeight.Medium,
            color = colors.labelPrimary,
            maxLines = 1,
            softWrap = false,
            overflow = TextOverflow.Ellipsis
        )
    }
}

/**
 * Glass tile carrying the WD mark impression. Pure Compose: a layered surface,
 * a thin highlight edge across the top and the monogram drawn as strokes with
 * the accent token. No bitmap, no third-party asset, no colour gradient.
 */
@Composable
fun WdMarkTile(
    modifier: Modifier = Modifier,
    size: Dp = 28.dp,
    tint: Color = WdTheme.colors.accent,
    container: Color = WdTheme.colors.elevatedSurface,
    borderColor: Color = WdTheme.colors.accentBorder
) {
    val colors = WdTheme.colors
    val shape = RoundedCornerShape(WdRadius.small)
    Box(
        modifier = modifier
            .size(size)
            .clip(shape)
            .background(container)
            .border(0.5.dp, borderColor, shape)
    ) {
        Canvas(modifier = Modifier.size(size)) {
            val w = this.size.width
            val h = this.size.height
            // Thin highlight edge on top of the tile: depth without a gradient fill.
            drawLine(
                brush = Brush.verticalGradient(
                    colors = listOf(colors.highlightEdge, Color.Transparent),
                    startY = 0f,
                    endY = h * 0.35f
                ),
                start = Offset(w * 0.12f, 0.75f),
                end = Offset(w * 0.88f, 0.75f),
                strokeWidth = 1.5f,
                cap = StrokeCap.Round
            )

            val stroke = Stroke(
                width = this.size.minDimension * 0.085f,
                cap = StrokeCap.Round,
                join = StrokeJoin.Round
            )
            // "W": four descending/ascending strokes.
            val markW = Path().apply {
                moveTo(w * 0.14f, h * 0.36f)
                lineTo(w * 0.23f, h * 0.64f)
                lineTo(w * 0.31f, h * 0.45f)
                lineTo(w * 0.39f, h * 0.64f)
                lineTo(w * 0.48f, h * 0.36f)
            }
            // "D": stem plus a rounded bowl, closed back to the stem.
            val markD = Path().apply {
                moveTo(w * 0.58f, h * 0.36f)
                lineTo(w * 0.66f, h * 0.36f)
                cubicTo(w * 0.84f, h * 0.36f, w * 0.84f, h * 0.64f, w * 0.66f, h * 0.64f)
                lineTo(w * 0.58f, h * 0.64f)
                lineTo(w * 0.58f, h * 0.36f)
            }
            drawPath(markW, color = tint, style = stroke)
            drawPath(markD, color = tint, style = stroke)
        }
    }
}

/**
 * Status card: a grouped inset card with a state dot, the current status and a
 * secondary instruction line. Replaces the earlier floating pill chip.
 */
@Composable
fun WdStatusHero(
    status: String,
    modifier: Modifier = Modifier,
    detail: String? = null,
    active: Boolean = false
) {
    val colors = WdTheme.colors
    val dotColor = if (active) colors.success else colors.accent
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(WdRadius.grouped),
        color = colors.groupedSurface,
        border = androidx.compose.foundation.BorderStroke(1.dp, colors.hairline)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = WdSpacing.lg, vertical = WdSpacing.lg),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(WdSpacing.md)
        ) {
            Box(
                modifier = Modifier
                    .size(10.dp)
                    .background(dotColor, shape = androidx.compose.foundation.shape.CircleShape)
            )
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = status,
                    style = WdType.body,
                    fontWeight = FontWeight.SemiBold,
                    color = colors.labelPrimary
                )
                if (detail != null) {
                    Spacer(modifier = Modifier.height(WdSpacing.xs))
                    Text(
                        text = detail,
                        style = WdType.footnote,
                        color = colors.labelSecondary
                    )
                }
            }
        }
    }
}

/**
 * Maps the WD tokens onto a Material 3 scheme so the not-yet-migrated sections
 * (PHASE 2) keep resolving the same surfaces and labels they use today.
 */
fun wdColorScheme(colors: WdColors, isDark: Boolean): ColorScheme {
    val base = if (isDark) darkColorScheme() else lightColorScheme()
    return base.copy(
        primary = colors.accent,
        onPrimary = colors.background,
        background = colors.background,
        onBackground = colors.labelPrimary,
        surface = colors.groupedSurface,
        onSurface = colors.labelPrimary,
        surfaceVariant = colors.elevatedSurface,
        onSurfaceVariant = colors.labelSecondary,
        outline = colors.hairline,
        outlineVariant = colors.separatorStrong,
        error = colors.destructive
    )
}

/**
 * App-wide theme entry point: resolves the appearance-dependent token set and
 * installs both the WD tokens and the matching Material 3 scheme.
 */
@Composable
fun WdAppTheme(
    isDark: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colors = rememberWdColors(isDark)
    CompositionLocalProvider(LocalWdColors provides colors) {
        androidx.compose.material3.MaterialTheme(
            colorScheme = wdColorScheme(colors, isDark),
            content = content
        )
    }
}
