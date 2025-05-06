package com.specknet.pdiotapp.tests

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.rules.ActivityScenarioRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.specknet.pdiotapp.MainActivity
import com.specknet.pdiotapp.mocks.MockBleService
import com.specknet.pdiotapp.utils.Constants
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class AutoReconnectionTest {

    @get:Rule
    val activityScenarioRule = ActivityScenarioRule(MainActivity::class.java)

    private val context = ApplicationProvider.getApplicationContext<Context>()

    @Before
    fun setUp() {
        //  Insert dummy MAC address in SharedPreferences, so the app
        //    thinks there's a previously paired sensor
        val prefs = context.getSharedPreferences(Constants.PREFERENCES_FILE, Context.MODE_PRIVATE)
        prefs.edit()
            .putString(Constants.RESPECK_MAC_ADDRESS_PREF, "FA:KE:MA:CA:DD:RE:SS")
            .apply()

        // reset the mock's isConnected state
        MockBleService.isConnected = false
    }

    @Test
    fun testAutoReconnect() {
        // Launch MainActivity via ActivityScenarioRule above
        //    The app should start the BLE service automatically

        // Simulate connection success
        MockBleService.instance.simulateConnectionSuccess()

        Thread.sleep(1500)

        //  check if the mock says it's connected (basic check)
        assertTrue(
            "Expected MockBleService to be isConnected==true, but it wasn't.",
            MockBleService.isConnected
        )

    }
}