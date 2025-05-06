package com.specknet.pdiotapp.mocks

import android.content.Context
import android.content.Intent
import android.util.Log
import androidx.test.core.app.ApplicationProvider
import com.specknet.pdiotapp.utils.Constants
import com.specknet.pdiotapp.utils.RESpeckLiveData
import java.io.Serializable

/**
 * Utility object to emulate sensor broadcasts to test classification logic.
 */
object MockSensorBroadcast {

    private val context = ApplicationProvider.getApplicationContext<Context>()

    /**
     * Sends an "action = ACTION_RESPECK_LIVE_BROADCAST" intent with the given sensor data.
     */
    fun sendRespeckData(accelX: Float, accelY: Float, accelZ: Float) {
        val intent = Intent(Constants.ACTION_RESPECK_LIVE_BROADCAST)
        val liveData = RESpeckLiveData(
            accelX = accelX,
            accelY = accelY,
            accelZ = accelZ,
            gyro = RESpeckLiveData.Gyro(0f, 0f, 0f), // fill in if needed
            phoneTimestamp = System.currentTimeMillis()
        )

        Log.d("MockSensorBroadcast", "Sending Respeck data broadcast: x=$accelX, y=$accelY, z=$accelZ")
        intent.putExtra(Constants.RESPECK_LIVE_DATA, liveData as Serializable)

        context.sendBroadcast(intent)

        context.sendBroadcast(intent) 
    }

    // Similarly, we could define sendThingyData(...) if needed
}