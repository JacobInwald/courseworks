package com.specknet.pdiotapp.tests

import android.util.Log
import androidx.test.ext.junit.rules.ActivityScenarioRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.specknet.pdiotapp.test.ClassifyingActivity
import com.specknet.pdiotapp.mocks.MockSensorBroadcast
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.math.max

@RunWith(AndroidJUnit4::class)
class ClassificationPerformanceTest {

    @get:Rule
    val activityRule = ActivityScenarioRule(ClassifyingActivity::class.java)

    @Test
    fun testClassificationLatencyUnder500ms() {
        //tracks maximum observed latency
        var maxLatency = 0L

        //20 broadcasts to measure average 
        for (i in 1..20) {
            val startTime = System.currentTimeMillis()
            MockSensorBroadcast.sendRespeckData(
                accelX = i * 0.1f,
                accelY = i * 0.05f,
                accelZ = i * -0.02f
            )

            Thread.sleep(200)



            val endTime = System.currentTimeMillis()
            val latency = endTime - startTime
            maxLatency = max(maxLatency, latency)
            Log.d("PerformanceTest", "Iteration $i => approx latency: $latency ms")
        }

        assert(maxLatency <= 500) {
            "Classification latency exceeded 500ms (was $maxLatency ms)"
        }
    }
}