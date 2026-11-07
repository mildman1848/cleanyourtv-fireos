package io.github.maxhayim.tvhub.data

import io.github.maxhayim.tvhub.R
import io.github.maxhayim.tvhub.TvHubApp

import java.io.BufferedInputStream
import java.io.FilterInputStream
import java.io.IOException
import java.io.InputStream
import java.net.HttpURLConnection
import java.net.SocketTimeoutException
import java.net.URL
import java.net.UnknownHostException
import java.util.zip.GZIPInputStream
import javax.net.ssl.SSLException

/** Plain HttpURLConnection: no extra library for a few GETs. Gzip is detected by its magic bytes, so .xml.gz guides work. */
object Http {
    class HttpError(message: String) : IOException(message)

    fun open(url: String, maxBytes: Long, headers: Map<String, String> = emptyMap()): InputStream {
        var current = url
        repeat(6) {
            val c = URL(current).openConnection() as HttpURLConnection
            c.connectTimeout = 15_000
            c.readTimeout = 30_000
            c.instanceFollowRedirects = false
            c.setRequestProperty("User-Agent", headers["User-Agent"] ?: "TVHub/1.0 (Android TV)")
            c.setRequestProperty("Accept-Encoding", "gzip")
            headers.forEach { (k, v) -> if (k != "User-Agent") c.setRequestProperty(k, v) }
            val code = try { c.responseCode } catch (e: IOException) { c.disconnect(); throw friendly(e) }
            if (code in 300..399) {
                val loc = c.getHeaderField("Location")
                c.disconnect()
                if (loc.isNullOrEmpty()) throw HttpError(TvHubApp.str(R.string.ht_redirect_nowhere))
                current = URL(URL(current), loc).toString()
                if (!current.startsWith("http://") && !current.startsWith("https://")) throw HttpError(TvHubApp.str(R.string.ht_redirect_bad))
                return@repeat
            }
            if (code !in 200..299) {
                c.disconnect()
                throw HttpError(
                    when (code) {
                        401, 403 -> TvHubApp.str(R.string.ht_refused, code)
                        404 -> TvHubApp.str(R.string.ht_404)
                        else -> TvHubApp.str(R.string.ht_other, code)
                    }
                )
            }
            val raw = BufferedInputStream(Limited(c.inputStream, maxBytes), 64 * 1024)
            raw.mark(2)
            val b0 = raw.read(); val b1 = raw.read()
            raw.reset()
            return if (b0 == 0x1f && b1 == 0x8b) Limited(GZIPInputStream(raw, 64 * 1024), maxBytes * 8) else raw
        }
        throw HttpError(TvHubApp.str(R.string.ht_redirects))
    }

    fun text(url: String, maxBytes: Long = 4L * 1024 * 1024): String = open(url, maxBytes).use { it.readBytes().toString(Charsets.UTF_8) }

    fun friendly(e: Throwable): IOException = when (e) {
        is HttpError -> e
        is UnknownHostException -> HttpError(TvHubApp.str(R.string.ht_unknown_host))
        is SocketTimeoutException -> HttpError(TvHubApp.str(R.string.ht_timeout))
        is SSLException -> HttpError(TvHubApp.str(R.string.ht_ssl))
        is java.net.ConnectException -> HttpError(TvHubApp.str(R.string.ht_connect))
        is TooLarge -> HttpError(e.message ?: TvHubApp.str(R.string.ht_too_large))
        is IOException -> HttpError(TvHubApp.str(R.string.ht_network, e.javaClass.simpleName))
        else -> HttpError(TvHubApp.str(R.string.ht_unexpected, e.javaClass.simpleName))
    }

    class TooLarge(message: String) : IOException(message)

    /** Stops a download that grows past what a TV should hold. */
    private class Limited(input: InputStream, private val max: Long) : FilterInputStream(input) {
        private var count = 0L
        override fun read(): Int = super.read().also { if (it >= 0) bump(1) }
        override fun read(b: ByteArray, off: Int, len: Int): Int = super.read(b, off, len).also { if (it > 0) bump(it.toLong()) }
        private fun bump(n: Long) { count += n; if (count > max) throw TooLarge(TvHubApp.str(R.string.ht_larger_than, (max / (1024 * 1024)).toInt())) }
    }
}
