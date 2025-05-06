package com.specknet.pdiotapp.test

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Bundle
import android.os.Handler
import android.os.HandlerThread
import android.os.Looper
import android.util.Log
import android.view.KeyEvent
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.specknet.pdiotapp.R
import com.specknet.pdiotapp.utils.Activity
import com.specknet.pdiotapp.utils.Constants
import com.specknet.pdiotapp.utils.CountUpTimer
import com.specknet.pdiotapp.utils.ExtraUtils
import com.specknet.pdiotapp.utils.FileManager
import com.specknet.pdiotapp.utils.Model
import com.specknet.pdiotapp.utils.RESpeckLiveData
import com.specknet.pdiotapp.utils.Resp
import com.specknet.pdiotapp.utils.ThingyLiveData
import org.tensorflow.lite.Interpreter
import org.tensorflow.lite.support.common.FileUtil
import kotlin.math.pow
import kotlin.math.sqrt


class ClassifyingActivity : AppCompatActivity() {

    // Model setup
    private val dyn_stat_model by lazy {
        Model(Interpreter(
            FileUtil.loadMappedFile(this,  "dynamic_static_model.tflite")),
            6, 50, listOf(-0.06398553731634682, -0.50710438092695, 0.05702876667031249, -0.3801799368182589, -0.02861014707186093, 0.09644849800209886) , listOf(0.4804117697431912, 0.5289800472112214, 0.5619486513585968, 0.5838506163647519, 0.5240864795266389, 0.6206116496287748))
    }

    private val dyn_model by lazy {
        Model(Interpreter(
            FileUtil.loadMappedFile(this,  "dynamic_model.tflite")),
            6, 50, listOf(0.01223499344469345, -0.8551501515487265, -0.002236249308341817, -0.8246063884952255, 0.03586319234491295, 0.10359812441459809) , listOf(0.3570423209673035, 0.5153255673560071, 0.3278134157398535, 0.5845630469490963, 0.48489546739077016, 0.4242086952627751))
    }

    private val stat_model by lazy {
        Model(Interpreter(
            FileUtil.loadMappedFile(this,  "static_model.tflite")),
            6, 50, listOf(-0.09458632783469469, -0.3354974586892178, 0.08712433048268704, -0.18547441099973364, -0.0534533444137228, 0.0874577020352516) , listOf(0.5251983242486463, 0.45740494674800664, 0.6404483957590427, 0.4455314731788191, 0.5424212978418669, 0.6922989517511733))
    }


    private val resp_model by lazy {
        Model(Interpreter(
            FileUtil.loadMappedFile(this, "resp_model.tflite")),
            3, 50, listOf(-0.09115067049311343, -0.31081814538139524, 0.0873735311397047) , listOf(0.5362477955256391, 0.4541727252902214, 0.6463643194257788))
    }

    // Data Stream Setup
    lateinit var respeckReceiver: BroadcastReceiver
    lateinit var thingyReceiver: BroadcastReceiver
    lateinit var looperRespeck: Looper
    lateinit var looperThingy: Looper

    val respeckFilterTest = IntentFilter(Constants.ACTION_RESPECK_LIVE_BROADCAST)
    val thingyFilterTest = IntentFilter(Constants.ACTION_THINGY_BROADCAST)

    lateinit var stream: Array<FloatArray>
    private var bufferSize: Int = 51
    private var inputSize: Int = 6

    lateinit var fileManager: FileManager

    // Background classification task
    var saveActivityData: Boolean = false
    val sampleSize = 3  // defines the sample size to average over

    // physical actions
    var physicalActivity = Array(sampleSize) { Activity.UNDEFINED}
    // Gets the mode of the physical activity array
    var curAction: () -> Activity = {physicalActivity.groupingBy { it }.eachCount().maxByOrNull {it.value}?.key?:Activity.UNDEFINED}

    // respiratory signals
    var respSignals = Array(sampleSize) { Resp.UNDEFINED }
    // Gets the mode of the physical activity array
    var curResp: () -> Resp = {respSignals.groupingBy { it }.eachCount().maxByOrNull {it.value}?.key?:Resp.UNDEFINED}

    // Initialised a background task to update the two action arrays
    lateinit var mainHandler: Handler
    private val updateClassifyTextTask = object : Runnable {
        override fun run() {
            updatePhysicalActivity()
            updateRespSignals()
            save(curAction(), curResp())
            mainHandler.postDelayed(this, 500)
        }
    }


    lateinit var scheduledUpdate: CountUpTimer

    // Buttons
    lateinit var startRecordingButton: Button
    lateinit var stopRecordingButton: Button

    // Override functions

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        fileManager = FileManager(getExternalFilesDir(null), Activity)
        setContentView(R.layout.activity_classify)

        setupClickListeners()


        scheduledUpdate = object: CountUpTimer(1000) {
            override fun onTick(elapsedTime: Long) {
                updateClassifyText()
            }
        }
        scheduledUpdate.start()

        stream = Array(bufferSize) { FloatArray(inputSize) }

        respeckReceiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context, intent: Intent) {

                val action = intent.action

                if (action == Constants.ACTION_RESPECK_LIVE_BROADCAST) {

                    val liveData = intent.getSerializableExtra(Constants.RESPECK_LIVE_DATA) as RESpeckLiveData
                    Log.d("respeckLive", "onReceive: liveData = " + liveData)

                    stream[stream.size-1][0] = liveData.accelX
                    stream[stream.size-1][1] = liveData.accelY
                    stream[stream.size-1][2] = liveData.accelZ

                    Log.d("respeckLive", "onReceive: Updated Stream")

                    updateStream()
                }
            }
        }

        val handlerThreadRespeck = HandlerThread("bgThreadRespeckClassify")
        handlerThreadRespeck.start()
        looperRespeck = handlerThreadRespeck.looper
        val handlerRespeck = Handler(looperRespeck)
        this.registerReceiver(respeckReceiver, respeckFilterTest, null, handlerRespeck)


        thingyReceiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context, intent: Intent) {

                val action = intent.action

                if (action == Constants.ACTION_THINGY_BROADCAST) {

                    val liveData = intent.getSerializableExtra(Constants.THINGY_LIVE_DATA) as ThingyLiveData
                    Log.d("thingyLive", "onReceive: thingyLiveData = " + liveData)

                    stream[stream.size-1][3] = liveData.accelX
                    stream[stream.size-1][4] = liveData.accelY
                    stream[stream.size-1][5] = liveData.accelZ

                    Log.d("thingyLive", "onReceive: Updated Stream")

                    updateStream()

                }
            }
        }

        val handlerThreadThingy = HandlerThread("bgThreadThingyClassify")
        handlerThreadThingy.start()
        looperThingy = handlerThreadThingy.looper
        val handlerThingy = Handler(looperThingy)
        this.registerReceiver(thingyReceiver, thingyFilterTest, null, handlerThingy)



        mainHandler = Handler(Looper.getMainLooper())
        mainHandler.postDelayed(updateClassifyTextTask, 0)
    }


    override fun onDestroy() {
        super.onDestroy()
        unregisterReceiver(respeckReceiver)
        unregisterReceiver(thingyReceiver)

        fileManager.close()

        looperRespeck.quit()
        looperThingy.quit()
        scheduledUpdate.stop()
    }


    // Setup methods

    fun setupClickListeners() {
        startRecordingButton = findViewById(R.id.classify_start_button)
        stopRecordingButton = findViewById(R.id.classify_stop_button)

        startRecordingButton.setOnClickListener {
            saveActivityData = true
        }

        stopRecordingButton.setOnClickListener {
            fileManager.close()
            saveActivityData = false
        }

    }


    // Update methods

    fun updatePhysicalActivity() {
        ExtraUtils.moveLeft(physicalActivity, Activity.UNDEFINED)
        physicalActivity[physicalActivity.size-1] = getCurrentAction()
    }

    fun updateRespSignals() {
        ExtraUtils.moveLeft(respSignals, Resp.UNDEFINED)
        respSignals[respSignals.size-1] = getCurrentResp()
    }

    fun updateClassifyText(){
        val physicalText = findViewById<TextView>(R.id.physical_classify_text)
        val respText = findViewById<TextView>(R.id.resp_classify_text)

        physicalText.setText(curAction().toStringResource())
        respText.setText(curResp().toStringResource())
    }

    // Functionality

    fun updateStream() {
        Log.d("stream", "streamCallback: stream current is " + stream[stream.size-1].joinToString(", "))
        // Move to next item if array is full
        if (stream[stream.size-1].all{it != 0f}) {
            Log.d("stream", "streamCallback: Attempting rolling window")
            stream = ExtraUtils.moveLeft(stream, FloatArray(inputSize))
        }

        Log.d("stream", "streamCallback: Moved data, current is "+  stream.map{it.joinToString(",")}.joinToString (","))

    }

    // Action recording and other
    fun getCurrentAction() : Activity {
        Log.d("classify", "updateClassifyText: Called")

        if (stream[0].all { it == 0f })
            return Activity.UNDEFINED

        // Check dynamic or static
        var out: FloatArray
        val static: Boolean
        out = dyn_stat_model.classify(stream, Array(1){FloatArray(2)})[0]

        if (out[0] > out[1]) {// Dynamic
            static = false
            out = dyn_model.classify(stream, Array(1) {FloatArray(6)})[0]
        }
        else {
            static = true
            out = stat_model.classify(stream, Array(1) {FloatArray(5)})[0]
        }

        Log.d("classify", "updateClassifyText: classified! " + out.joinToString(", "))

        return Activity.fromOneHot(out, static)
    }

    // Remember that the stream may be different here
    fun getCurrentResp() : Resp {
        Log.d("classify", "updateClassifyText: Called")

        if (Activity.isDynamic(curAction()) || stream[0].all { it == 0f })
            return Resp.UNDEFINED

        // builds the input as a the first three elements of each item in the list

        val out = resp_model.classify(stream, Array(1) {FloatArray(8)})[0]

        Log.d("classify", "updateClassifyText: classified! " + out.joinToString(", "))

        return Resp.fromOneHot(out)
    }


    fun save(act: Activity = Activity.UNDEFINED,
             resp: Resp = Resp.UNDEFINED) {

        if (!saveActivityData)
            return

        fileManager.enum = Activity
        fileManager.write(act)
        fileManager.enum = Resp
        fileManager.write(resp)

    }

}