package com.specknet.pdiotapp.tests

import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.rules.ActivityScenarioRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.assertion.ViewAssertions.matches
import androidx.test.espresso.matcher.ViewMatchers.withId
import androidx.test.espresso.matcher.ViewMatchers.withText
import com.specknet.pdiotapp.R
import com.specknet.pdiotapp.test.ClassifyingActivity
import com.specknet.pdiotapp.mocks.MockSensorBroadcast
import com.specknet.pdiotapp.mocks.StubModel
import com.specknet.pdiotapp.utils.Constants
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ClassificationDisplayConsistencyTest {

    @get:Rule
    val activityScenarioRule = ActivityScenarioRule(ClassifyingActivity::class.java)

    @Before
    fun setUp() {
        // your app references StubModel automatically in debug builds.
        StubModel.cycleLabels = true
        StubModel.labels = listOf("Walking", "Running")
    }

    @Test
    fun testClassificationUpdatesWithinOneSecond() {
        // Send initial sensor data => should produce "Walking"
        MockSensorBroadcast.sendRespeckData(0.1f, 0.2f, 0.3f)
        Thread.sleep(800)  // Wait up to 1s

        // Check if the UI label reads "Walking"
        onView(withId(R.id.physical_classify_text))
            .check(matches(withText("Walking")))

        // Send sensor data => should produce "Running"
        MockSensorBroadcast.sendRespeckData(-0.5f, 0.1f, 0.0f)
        Thread.sleep(800)

        // Check if the UI label reads "Running"
        onView(withId(R.id.physical_classify_text))
            .check(matches(withText("Running")))
    }
}