package com.specknet.pdiotapp.test

import android.os.Bundle
import android.text.format.Time
import android.util.Log
import android.widget.DatePicker
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.github.mikephil.charting.charts.BarChart
import com.github.mikephil.charting.data.BarData
import com.github.mikephil.charting.data.BarDataSet
import com.github.mikephil.charting.data.BarEntry
import com.github.mikephil.charting.formatter.IndexAxisValueFormatter
import com.specknet.pdiotapp.R
import com.specknet.pdiotapp.utils.Activity
import com.specknet.pdiotapp.utils.ActivityEntry
import com.specknet.pdiotapp.utils.CountUpTimer
import com.specknet.pdiotapp.utils.FileManager
import com.specknet.pdiotapp.utils.IOutputEnum
import com.specknet.pdiotapp.utils.IOutputEnumCompanion
import com.specknet.pdiotapp.utils.Resp
import org.w3c.dom.Text
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.concurrent.TimeUnit
import kotlin.math.min
import kotlin.time.Duration
import kotlin.time.Duration.Companion.hours
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.seconds
import kotlin.time.DurationUnit


class LogbookActivity: AppCompatActivity() {

    lateinit var logbook_names: TextView
    lateinit var logbook_values: TextView

    lateinit var bar_1: ProgressBar
    lateinit var bar_1_time_text: TextView
    lateinit var bar_1_text: TextView

    lateinit var bar_2: ProgressBar
    lateinit var bar_2_time_text: TextView
    lateinit var bar_2_text: TextView

    lateinit var bar_3: ProgressBar
    lateinit var bar_3_time_text: TextView
    lateinit var bar_3_text: TextView


    lateinit var datePicker: DatePicker
    var date: () -> Date = { datePicker.getDate() }
    lateinit var fileManager: FileManager
    lateinit var scheduledUpdate: CountUpTimer



    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        fileManager = FileManager(getExternalFilesDir(null), Activity)

        setContentView(R.layout.activity_logbook)

        logbook_names = findViewById(R.id.logbook_names)
        logbook_values = findViewById(R.id.logbook_values)

        bar_1 = findViewById(R.id.bar_1)
        bar_1_time_text = findViewById(R.id.bar_1_time_text)
        bar_1_text = findViewById(R.id.bar_1_text)

        bar_2 = findViewById(R.id.bar_2)
        bar_2_time_text = findViewById(R.id.bar_2_time_text)
        bar_2_text = findViewById(R.id.bar_2_text)

        bar_3 = findViewById(R.id.bar_3)
        bar_3_time_text = findViewById(R.id.bar_3_time_text)
        bar_3_text = findViewById(R.id.bar_3_text)

        datePicker = findViewById(R.id.date_picker)

        val today = Calendar.getInstance()
        datePicker.init(today.get(Calendar.YEAR), today.get(Calendar.MONTH), today.get(Calendar.DAY_OF_MONTH)) {
                view, year, month, day ->
        }

        scheduledUpdate = object: CountUpTimer(1000) {
            override fun onTick(elapsedTime: Long) {
                updateGraph()
                updateLogbook()
            }
        }
        scheduledUpdate.start()

    }



    fun timeToString(time: Long): String{
        val hours = time / 3600
        val minutes = (time % 3600) / 60
        val seconds = time % 60

        return "%02d:%02d:%02d".format(hours, minutes, seconds)
    }

    fun updateLogbook() {
        var log = ""
        var values = ""

        // Activities
        fileManager.enum = Activity
        val actMap = fileManager.parse(date()).sum()
        for(a in Activity.values().drop(1)) {
            log += getString(R.string.logbook_entry, a.toString())
            values += getString(
                R.string.logbook_value,
                timeToString(actMap.get(a) ?: 0)
            )
        }
        log += "\n"
        values += "\n"
        // Activities
        fileManager.enum = Resp
        val resMap = fileManager.parse(date()).sum()
        for(r in Resp.values().drop(1)) {
            log += getString(R.string.logbook_entry, r.toString())
            values += getString(
                R.string.logbook_value,
                timeToString(resMap.get(r) ?: 0)
            )
        }
        log+="\n\n\n\n\n\n\n"
        values+="\n\n\n\n\n\n"
        logbook_names.setText(getString(R.string.logbook_title, log))
        logbook_values.setText(getString(R.string.logbook_value_header, values))
    }


    fun updateGraph() {
        fileManager.enum = Activity
        val actMap = fileManager.parse(date()).sum()
        actMap.remove(Activity.UNDEFINED)

        Log.d("graph", "Summed activities")
        val max_1 = actMap.maxByOrNull { it.value }
        if (max_1 != null) actMap.remove(max_1.key)
        val max_2 = actMap.maxByOrNull { it.value }
        if (max_2 != null) actMap.remove(max_2.key)
        val max_3 = actMap.maxByOrNull { it.value }
        if (max_3 != null) actMap.remove(max_3.key)

        if (max_1 == null || max_2 == null || max_3 == null) {
            bar_1.progress = 10
            bar_1_time_text.text = timeToString(0)
            bar_1_text.setText(Activity.UNDEFINED.toStringResource())
            bar_2.progress = 10
            bar_2_time_text.text = timeToString(0)
            bar_2_text.setText(Activity.UNDEFINED.toStringResource())
            bar_3.progress = 10
            bar_3_time_text.text = timeToString(0)
            bar_3_text.setText(Activity.UNDEFINED.toStringResource())
            return
        }

        bar_1.progress = 95
        bar_1_time_text.text = timeToString(max_1.value)
        bar_1_text.setText(max_1.key.toStringResource())

        bar_2.progress = (95 * (max_2.value.toDouble() / max_1.value)).toInt()
        bar_2_time_text.text = timeToString(max_2.value)
        bar_2_text.setText(max_2.key.toStringResource())

        bar_3.progress = (95 * (max_3.value.toDouble() / max_1.value)).toInt()
        bar_3_time_text.text = timeToString(max_3.value)
        bar_3_text.setText(max_3.key.toStringResource())

    }


}

private fun List<ActivityEntry>.sum(): MutableMap<IOutputEnum, Long> {
    val actMap = mutableMapOf<IOutputEnum, Long>()
    var diff: Long

    if (this.size == 0) return actMap

    // Get sum of activities
    for (entry in this) {
        if (entry.end.before(entry.start))
            diff = TimeUnit.MILLISECONDS.toSeconds(entry.start.time - entry.end.time)
        else
            diff = TimeUnit.MILLISECONDS.toSeconds(entry.end.time - entry.start.time)
        Log.d("time", ""+ entry.start + " " + entry.end)
        actMap[entry.action] = (actMap.get(entry.action) ?: 0) + diff
    }
    return actMap
}

private fun DatePicker.getDate(): Date {
    val calendar = Calendar.getInstance()
    calendar.set(year, month, dayOfMonth)
    return calendar.time
}
