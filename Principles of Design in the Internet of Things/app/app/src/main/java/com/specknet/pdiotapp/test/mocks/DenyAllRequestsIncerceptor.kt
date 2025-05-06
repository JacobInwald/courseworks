package com.specknet.pdiotapp.mocks

import okhttp3.Interceptor
import okhttp3.Response
import java.io.IOException

/**
 * Intercepts all outbound HTTP requests and fails if any are attempted.
 */
class DenyAllRequestsInterceptor : Interceptor {
    @Throws(IOException::class)
    override fun intercept(chain: Interceptor.Chain): Response {
        // Any attempt to proceed with an HTTP request triggers an error
        throw IOException("Network usage detected in test mode! No external calls allowed.")
    }
}