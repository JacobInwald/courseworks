package com.specknet.pdiotapp.mocks

import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.IBinder
import android.util.Log
import androidx.localbroadcastmanager.content.LocalBroadcastManager
import com.specknet.pdiotapp.utils.Constants

/**
 * A mock BLE service that simulates connecting to a Respeck/Thingy sensor.
 * Allows test code to inject success/failure states without real hardware.
 */

class MockBleService : Service() {

    // We use a companion object so the test can easily call MockBleService.instance to manipulate states.
    companion object {
        private var _instance: MockBleService? = null
        val instance: MockBleService
            get() = _instance
                ?: throw IllegalStateException("MockBleService not initialized or not running.")

        // Optional: track a global 'isConnected' or 'isFail' for debugging
        var isConnected: Boolean = false
    }

    override fun onCreate() {
        super.onCreate()
        _instance = this
        Log.d("MockBleService", "Mock service created.")
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        super.onDestroy()
        _instance = null
        Log.d("MockBleService", "Mock service destroyed.")
    }

    /**
     * sims a successful sensor connection
     */
    fun simulateConnectionSuccess() {
        isConnected = true
        Log.d("MockBleService", "Simulating BLE connection success.")

        // Broadcast a "connected" event exactly like real code might do:
        val broadcastIntent = Intent(Constants.ACTION_RESPECK_CONNECTED)
        // Possibly attach extras if the real code expects them:
        // broadcastIntent.putExtra("macAddress", "FA:KE:MA:CA:DD:RE:SS")
        LocalBroadcastManager.getInstance(this).sendBroadcast(broadcastIntent)
    }

    /**
     * sims a connection failure
     */
    fun simulateConnectionFailure() {
        isConnected = false
        Log.d("MockBleService", "Simulating BLE connection failure.")

        // For failure, you might broadcast a "disconnected" or "failed" action.
        val broadcastIntent = Intent(Constants.ACTION_RESPECK_DISCONNECTED)
        LocalBroadcastManager.getInstance(this).sendBroadcast(broadcastIntent)
    }

    /**
     * handles start commands (like the real service):
     */
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // For a real BLE service, we'd parse sensor ID from SharedPreferences or Intent
        // This is a mock, so do nothing. Tests will call simulateConnectionSuccess/Failure themselves.
        Log.d("MockBleService", "onStartCommand called (mock).")
        return START_NOT_STICKY
    }
}