package io.github.maxhayim.tvhub.ui

import io.github.maxhayim.tvhub.R

import android.app.AlertDialog
import android.view.View
import android.widget.ScrollView
import io.github.maxhayim.tvhub.model.SourceConfig
import io.github.maxhayim.tvhub.model.SourceStatus
import io.github.maxhayim.tvhub.model.SourceType
import io.github.maxhayim.tvhub.ui.Ui.dp

/** Every configured source with its last result, and the way to add, edit, refresh or remove one. */
class SourcesScreen(host: MainActivity) : Screen(host) {
    private val actions = Ui.horizontal(ctx, 16)
    private val list = Ui.vertical(ctx, 10)

    override val view: View = ScrollView(ctx).apply {
        clipChildren = false; clipToPadding = false
        isVerticalScrollBarEnabled = false
        val col = Ui.vertical(ctx, 18)
        col.addView(Ui.text(ctx, str(R.string.src_title), 30f, bold = true))
        col.addView(Ui.text(ctx, str(R.string.src_intro), 16f, Ui.DIM, lines = 2))
        actions.addView(Ui.button(ctx, str(R.string.src_add)) { addDialog() })
        actions.addView(Ui.button(ctx, str(R.string.src_refresh_all)) { repo.refreshAll() })
        col.addView(actions)
        col.addView(list)
        addView(col, Ui.lp())
    }

    override fun onShow() {
        watch(repo.sources) { build(it) }
        watch(repo.refresh) { if (!it.running) repo.load() }
    }

    private fun build(sources: List<Pair<SourceConfig, SourceStatus>>) {
        val hadFocus = list.findFocus() != null
        list.removeAllViews()
        if (sources.isEmpty()) list.addView(Ui.text(ctx, str(R.string.src_none), 18f, Ui.DIM))
        sources.forEach { (s, st) ->
            val row = Ui.vertical(ctx, 4).apply {
                isFocusable = true; isClickable = true
                background = Ui.focusable(ctx)
                setPadding(dp(20), dp(14), dp(20), dp(14))
                setOnClickListener { actionsFor(s) }
            }
            row.addView(Ui.text(ctx, s.name + if (!s.enabled) str(R.string.src_off_suffix) else "", 20f, if (s.enabled) Ui.TEXT else Ui.DIM, bold = true))
            row.addView(Ui.text(ctx, typeLabel(ctx, s.type), 14f, Ui.DIM))
            val line = when {
                !s.enabled -> str(R.string.src_turned_off)
                s.type == SourceType.APPS -> str(R.string.src_apps_line, plural(R.plurals.n_apps, s.packages.size))
                st.error != null -> st.error
                st.lastRefresh == 0L -> str(R.string.src_not_read)
                s.type == SourceType.XMLTV -> str(R.string.src_guide_line, plural(R.plurals.n_guide_channels, st.channelCount), Ui.dayTime(ctx, st.lastRefresh))
                st.skipped > 0 -> str(R.string.src_channels_line_skipped, plural(R.plurals.n_channels, st.channelCount), str(R.string.src_skipped, plural(R.plurals.n_entries, st.skipped)), Ui.dayTime(ctx, st.lastRefresh))
                else -> str(R.string.src_channels_line, plural(R.plurals.n_channels, st.channelCount), Ui.dayTime(ctx, st.lastRefresh))
            }
            row.addView(Ui.text(ctx, line, 15f, if (st.error != null && s.enabled) Ui.ERROR else Ui.DIM, lines = 2))
            list.addView(row)
        }
        if (hadFocus) list.getChildAt(0)?.requestFocus()
    }

    private fun actionsFor(s: SourceConfig) {
        val items = arrayOf(
            str(if (s.type == SourceType.APPS) R.string.src_choose_apps else R.string.src_edit),
            str(if (s.enabled) R.string.src_turn_off else R.string.src_turn_on),
            str(R.string.src_refresh_now),
            str(R.string.src_remove),
        )
        AlertDialog.Builder(ctx, android.R.style.Theme_DeviceDefault_Dialog_Alert)
            .setTitle(s.name)
            .setItems(items) { _, which ->
                when (which) {
                    0 -> SourceEditorActivity.start(ctx, s.type, s.id)
                    1 -> repo.saveSource(s.copy(enabled = !s.enabled))
                    2 -> repo.refreshAll()
                    3 -> AlertDialog.Builder(ctx, android.R.style.Theme_DeviceDefault_Dialog_Alert)
                        .setTitle(str(R.string.src_remove_title, s.name))
                        .setMessage(str(R.string.src_remove_msg))
                        .setPositiveButton(R.string.src_remove) { _, _ -> repo.deleteSource(s.id) }
                        .setNegativeButton(R.string.cancel, null).show()
                }
            }.show()
    }

    private fun addDialog() {
        val types = SourceType.entries
        AlertDialog.Builder(ctx, android.R.style.Theme_DeviceDefault_Dialog_Alert)
            .setTitle(R.string.src_add)
            .setItems(types.map { typeLabel(ctx, it) }.toTypedArray()) { _, i -> SourceEditorActivity.start(ctx, types[i], 0) }
            .show()
    }

    override fun focusFirst(): Boolean = actions.getChildAt(0)?.requestFocus() ?: false

    companion object {
        fun plural(c: android.content.Context, id: Int, n: Int): String = c.resources.getQuantityString(id, n, n)

        fun typeLabel(c: android.content.Context, t: SourceType): String = c.getString(when (t) {
            SourceType.M3U -> R.string.type_m3u
            SourceType.XMLTV -> R.string.type_xmltv
            SourceType.DISPATCHARR -> R.string.type_dispatcharr
            SourceType.HDHOMERUN -> R.string.type_hdhomerun
            SourceType.APPS -> R.string.type_apps
        })
    }
}
