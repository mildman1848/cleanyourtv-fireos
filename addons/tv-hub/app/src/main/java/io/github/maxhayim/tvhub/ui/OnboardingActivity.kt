package io.github.maxhayim.tvhub.ui

import io.github.maxhayim.tvhub.R

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.widget.ScrollView
import android.widget.TextView
import io.github.maxhayim.tvhub.TvHubApp
import io.github.maxhayim.tvhub.model.SourceType
import io.github.maxhayim.tvhub.ui.Ui.dp

/** First launch: pick any sources to add now, or skip. Every step is optional and can be done later in Sources. */
class OnboardingActivity : Activity() {
    private val repo get() = (application as TvHubApp).repo
    private val buttons = LinkedHashMap<SourceType, TextView>()
    private val labels = linkedMapOf(
        SourceType.M3U to R.string.onb_m3u,
        SourceType.XMLTV to R.string.onb_xmltv,
        SourceType.DISPATCHARR to R.string.onb_dispatcharr,
        SourceType.HDHOMERUN to R.string.onb_hdhomerun,
        SourceType.APPS to R.string.onb_apps,
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val col = Ui.vertical(this, 16).apply { setPadding(dp(96), dp(56), dp(96), dp(40)) }
        col.addView(Ui.text(this, getString(R.string.onb_welcome), 34f, bold = true))
        col.addView(Ui.text(this, getString(R.string.onb_intro), 18f, Ui.DIM, lines = 0))
        val list = Ui.vertical(this, 10)
        labels.forEach { (t, l) ->
            val b = Ui.button(this, getString(l)) { startActivityForResult(SourceEditorActivity.intent(this, t, 0), 1) }
            b.gravity = android.view.Gravity.START or android.view.Gravity.CENTER_VERTICAL
            buttons[t] = b
            list.addView(b, Ui.lp(dp(520), Ui.WRAP))
        }
        col.addView(list)
        val done = Ui.button(this, getString(R.string.onb_skip)) { finishSetup() }
        col.addView(done, Ui.lp(Ui.WRAP, Ui.WRAP).apply { topMargin = dp(12) })
        setContentView(ScrollView(this).apply { setBackgroundColor(Ui.BG); addView(col) })
        buttons.values.first().requestFocus()
        doneButton = done
    }

    private var doneButton: TextView? = null

    @Deprecated("Activity result API needs androidx.activity; the platform call is enough here")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (resultCode != RESULT_OK) return
        val t = data?.getStringExtra(SourceEditorActivity.EXTRA_TYPE)?.let { SourceType.valueOf(it) } ?: return
        buttons[t]?.let { it.text = "✓  " + labels[t]; it.setTextColor(Ui.OK) }
        doneButton?.setText(R.string.onb_done)
        doneButton?.requestFocus()
    }

    @Deprecated("Back is handled here so skipping setup still marks it done")
    override fun onBackPressed() { finishSetup() }

    private fun finishSetup() {
        repo.prefs.onboarded = true
        repo.load()
        finish()
    }
}
