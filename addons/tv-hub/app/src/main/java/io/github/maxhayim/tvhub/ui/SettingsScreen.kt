package io.github.maxhayim.tvhub.ui

import io.github.maxhayim.tvhub.R

import android.app.AlertDialog
import android.content.Intent
import android.view.View
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import io.github.maxhayim.tvhub.BuildConfig
import io.github.maxhayim.tvhub.ui.Ui.dp

class SettingsScreen(host: MainActivity) : Screen(host) {
    private val list = Ui.vertical(ctx, 8)

    override val view: View = ScrollView(ctx).apply {
        clipChildren = false; clipToPadding = false
        isVerticalScrollBarEnabled = false
        val col = Ui.vertical(ctx, 18)
        col.addView(Ui.text(ctx, str(R.string.set_title), 30f, bold = true))
        col.addView(list)
        addView(col, Ui.lp())
        build()
    }

    private fun build() {
        val p = repo.prefs
        list.removeAllViews()
        row(str(R.string.set_merge), str(if (p.mergeDuplicates) R.string.set_merge_on else R.string.set_merge_off)) {
            repo.setMerge(!p.mergeDuplicates); build()
        }
        row(str(R.string.set_guide_length), str(R.string.set_guide_length_detail, plural(R.plurals.n_days, p.guideDays))) {
            p.guideDays = when (p.guideDays) { 1 -> 2; 2 -> 3; 3 -> 7; else -> 1 }; build()
            Toast.makeText(ctx, str(R.string.set_next_refresh), Toast.LENGTH_SHORT).show()
        }
        row(str(R.string.set_refresh), if (p.refreshHours == 0) str(R.string.set_refresh_never) else str(R.string.set_refresh_hours, p.refreshHours)) {
            p.refreshHours = when (p.refreshHours) { 6 -> 12; 12 -> 24; 24 -> 0; else -> 6 }; build()
        }
        row(str(R.string.set_autoplay),
            str(if (p.autoPlay) R.string.set_autoplay_on else R.string.set_autoplay_off)) {
            p.autoPlay = !p.autoPlay; build()
        }
        row(str(R.string.set_animations), str(if (p.animations) R.string.set_on else R.string.set_animations_off)) {
            p.animations = !p.animations; build()
        }
        row(str(R.string.set_clear_recents), str(R.string.set_clear_recents_detail)) {
            repo.clearRecents(); Toast.makeText(ctx, str(R.string.set_cleared), Toast.LENGTH_SHORT).show()
        }
        row(str(R.string.set_setup_again), str(R.string.set_setup_again_detail)) {
            ctx.startActivity(Intent(ctx, OnboardingActivity::class.java))
        }
        row(str(R.string.set_about), str(R.string.set_about_detail, BuildConfig.VERSION_NAME)) { about() }
    }

    private fun row(title: String, sub: String, onClick: () -> Unit) {
        val r = Ui.vertical(ctx, 4).apply {
            isFocusable = true; isClickable = true
            background = Ui.focusable(ctx)
            setPadding(dp(20), dp(14), dp(20), dp(14))
            setOnClickListener {
                val idx = list.indexOfChild(this)
                onClick()
                list.getChildAt(idx)?.requestFocus()
            }
        }
        r.addView(Ui.text(ctx, title, 20f, bold = true))
        r.addView(Ui.text(ctx, sub, 15f, Ui.DIM, lines = 2))
        list.addView(r)
    }

    private fun about() {
        val text = ctx.assets.open("licenses.txt").bufferedReader().use { it.readText() }
        AlertDialog.Builder(ctx, android.R.style.Theme_DeviceDefault_Dialog_Alert)
            .setTitle(str(R.string.about_title, BuildConfig.VERSION_NAME))
            .setView(ScrollView(ctx).apply {
                isFocusable = true
                addView(TextView(ctx).apply { this.text = text; setTextColor(Ui.TEXT); textSize = 14f; setPadding(dp(28), dp(8), dp(28), dp(8)) })
            })
            .setPositiveButton(R.string.close, null).show()
    }

    override fun focusFirst(): Boolean = list.getChildAt(0)?.requestFocus() ?: false
}
