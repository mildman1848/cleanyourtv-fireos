package io.github.maxhayim.tvhub

import android.app.Application
import io.github.maxhayim.tvhub.data.Repository
import io.github.maxhayim.tvhub.ui.LogoLoader

class TvHubApp : Application() {
    lateinit var repo: Repository; private set
    lateinit var logos: LogoLoader; private set

    override fun onCreate() {
        super.onCreate()
        instance = this
        repo = Repository(this)
        logos = LogoLoader(this)
        repo.load()
    }

    companion object {
        private lateinit var instance: TvHubApp
        /** For code with no Context (network and parser errors); resolved at the moment of the error, in the TV's language. */
        fun str(@androidx.annotation.StringRes id: Int, vararg a: Any): String = instance.getString(id, *a)
        fun plural(@androidx.annotation.PluralsRes id: Int, n: Int): String = instance.resources.getQuantityString(id, n, n)
    }
}
