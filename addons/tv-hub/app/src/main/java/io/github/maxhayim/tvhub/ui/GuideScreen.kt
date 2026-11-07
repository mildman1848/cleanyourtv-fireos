package io.github.maxhayim.tvhub.ui

import io.github.maxhayim.tvhub.R

import android.app.AlertDialog
import android.view.View
import android.widget.FrameLayout
import android.widget.HorizontalScrollView
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import io.github.maxhayim.tvhub.model.Channel
import io.github.maxhayim.tvhub.model.Programme
import io.github.maxhayim.tvhub.ui.Ui.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/** The programme grid with a row of categories above it. */
class GuideScreen(host: MainActivity) : Screen(host) {
    private val grid = GuideView(ctx)
    private val chips = Ui.horizontal(ctx, 10)
    private val empty = Ui.text(ctx, "", 18f, Ui.DIM, lines = 4)
    private var channels: List<Channel> = emptyList()
    private var favs: Set<String> = emptySet()
    private var category = ALL
    private var shown: List<Channel> = emptyList()

    override val view: View = Ui.vertical(ctx, 14).apply {
        addView(Ui.text(ctx, str(R.string.nav_guide), 30f, bold = true))
        addView(HorizontalScrollView(ctx).apply { isHorizontalScrollBarEnabled = false; clipToPadding = false; setPadding(dp(4), dp(4), dp(4), dp(4)); addView(chips) })
        val frame = FrameLayout(ctx)
        frame.addView(grid, FrameLayout.LayoutParams(Ui.MATCH, Ui.MATCH))
        frame.addView(empty, FrameLayout.LayoutParams(Ui.MATCH, Ui.WRAP))
        addView(frame, Ui.lp(Ui.MATCH, 0, 1f))
    }

    init {
        grid.onNeed = { first, last ->
            val slice = shown.subList(first, last + 1).toList()
            val (from, to) = grid.timeRange
            host.scope.launch {
                val data = withContext(Dispatchers.IO) { repo.programmes(slice, from, to) }
                if (slice.firstOrNull()?.key == shown.getOrNull(first)?.key) grid.putProgrammes(first, last, data)
            }
        }
        grid.onSelect = { ch, p ->
            if (p == null || p.isOn(System.currentTimeMillis())) play(ch) else details(ch, p)
        }
        grid.onInfo = { ch, p -> details(ch, p) }
        grid.onLong = { ch ->
            val on = repo.toggleFavorite(ch.key)
            Toast.makeText(ctx, str(if (on) R.string.fav_added else R.string.fav_removed, ch.name), Toast.LENGTH_SHORT).show()
        }
    }

    override fun onShow() {
        watch(combine(repo.channels, repo.favorites) { c, f -> c to f }) { (c, f) ->
            val changed = c !== channels || (category == FAV && f != favs)
            channels = c; favs = f; grid.favorites = f
            if (changed) { buildChips(); applyCategory() }
        }
        watch(repo.guideVersion) { applyCategory() }
        // Keeps the now line moving and the grid starting at the current half hour.
        launch { while (true) { delay(60_000); grid.invalidate() } }
    }

    private fun buildChips() {
        chips.removeAllViews()
        val names = listOf(ALL, FAV) + channels.mapNotNull { it.group }.distinct()
        if (category !in names) category = ALL
        names.forEach { n ->
            chips.addView(Ui.text(ctx, label(n), 16f, if (n == category) Ui.TEXT else Ui.DIM, bold = true).apply {
                isFocusable = true; isClickable = true; isSelected = n == category; tag = n
                background = Ui.focusable(ctx, Ui.SURFACE, 20, Ui.SURFACE_2)
                setPadding(dp(18), dp(8), dp(18), dp(8))
                setOnClickListener { select(n); grid.requestFocus() }
                setOnFocusChangeListener { _, has -> if (has) select(n) }
                nextFocusDownId = View.NO_ID
            })
        }
    }

    /** ALL and FAV are keys, not text: group names come from the playlist and may be anything. */
    private fun label(n: String) = when (n) { ALL -> str(R.string.guide_all); FAV -> str(R.string.favorites); else -> n }

    private fun select(n: String) {
        if (n == category) return
        category = n
        for (i in 0 until chips.childCount) (chips.getChildAt(i) as TextView).let {
            val on = it.tag == n
            it.isSelected = on; it.setTextColor(if (on) Ui.TEXT else Ui.DIM)
        }
        applyCategory()
    }

    private fun applyCategory() {
        shown = when (category) {
            ALL -> channels
            FAV -> channels.filter { it.key in favs }
            else -> channels.filter { it.group == category }
        }
        grid.setData(shown, repo.prefs.guideDays)
        empty.text = when {
            shown.isNotEmpty() -> ""
            channels.isEmpty() -> str(R.string.guide_empty_no_channels)
            category == FAV -> str(R.string.guide_empty_no_favs)
            else -> str(R.string.guide_empty_group, category)
        }
        empty.visibility = if (shown.isEmpty()) View.VISIBLE else View.GONE
        grid.visibility = if (shown.isEmpty()) View.INVISIBLE else View.VISIBLE
    }

    private fun play(ch: Channel) {
        host.play(shown, shown.indexOfFirst { it.key == ch.key }.coerceAtLeast(0))
    }

    private fun details(ch: Channel, p: Programme?) {
        host.scope.launch {
            val desc = p?.let { withContext(Dispatchers.IO) { repo.description(it) } }
            val body = Ui.vertical(ctx, 10).apply { setPadding(dp(28), dp(12), dp(28), dp(8)) }
            body.addView(Ui.text(ctx, listOfNotNull(ch.number, ch.name).joinToString("  "), 16f, Ui.DIM))
            if (p != null) {
                body.addView(Ui.text(ctx, "${Ui.dayTime(ctx, p.start)} – ${Ui.time(ctx, p.stop)}", 16f, Ui.DIM))
                p.subtitle?.let { body.addView(Ui.text(ctx, it, 18f, bold = true, lines = 2)) }
                p.category?.let { body.addView(Ui.text(ctx, it, 14f, Ui.ACCENT)) }
                body.addView(Ui.text(ctx, desc ?: str(R.string.guide_no_desc), 17f, lines = 0))
            } else {
                body.addView(Ui.text(ctx, str(if (ch.epgIds.isEmpty()) R.string.guide_channel_no_info else R.string.guide_nothing_listed), 17f, lines = 0))
            }
            body.addView(Ui.text(ctx, str(R.string.guide_from, ch.sourceNames.joinToString(", ")), 14f, Ui.DIM))
            AlertDialog.Builder(ctx, android.R.style.Theme_DeviceDefault_Dialog_Alert)
                .setTitle(p?.title?.ifEmpty { null } ?: ch.name)
                .setView(ScrollView(ctx).apply { addView(body) })
                .setPositiveButton(R.string.watch_now) { _, _ -> play(ch) }
                .setNeutralButton(if (ch.key in favs) R.string.fav_remove_action else R.string.fav_add_action) { _, _ -> repo.toggleFavorite(ch.key) }
                .setNegativeButton(R.string.close, null)
                .show()
        }
    }

    override fun focusFirst(): Boolean = if (shown.isNotEmpty()) grid.requestFocus() else chips.getChildAt(0)?.requestFocus() ?: false

    private companion object { const val ALL = "\u0000all"; const val FAV = "\u0000fav" }
}
