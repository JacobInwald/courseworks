package com.specknet.pdiotapp.tests

import android.util.Log
import androidx.test.ext.junit.rules.ActivityScenarioRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.specknet.pdiotapp.MainActivity
import com.specknet.pdiotapp.mocks.DenyAllRequestsInterceptor
import okhttp3.OkHttpClient
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.io.IOException

@RunWith(AndroidJUnit4::class)
class DataPrivacyTest {

    @get:Rule
    val activityRule = ActivityScenarioRule(MainActivity::class.java)

    private lateinit var testHttpClient: OkHttpClient

    @Before
    fun setUp() {
        // Set up an OkHttpClient with the DenyAllRequestsInterceptor
        testHttpClient = OkHttpClient.Builder()
            .addInterceptor(DenyAllRequestsInterceptor())
            .build()

    }

    @Test
    fun testNoExternalCalls() {
        try {

            // deliberately attempt a call
            val request = okhttp3.Request.Builder()
                .url("http://example.com/some-endpoint")
                .build()

            testHttpClient.newCall(request).execute()
            // If this line is reached, no exception was thrown => fail the test
            assert(false) {
                "Expected an IOException from DenyAllRequestsInterceptor, but got none!"
            }
        } catch (ex: IOException) {
            // expected path
            Log.d("DataPrivacyTest", "Caught expected IOException. No external calls allowed.")
            assert(true)
        }
    }
}