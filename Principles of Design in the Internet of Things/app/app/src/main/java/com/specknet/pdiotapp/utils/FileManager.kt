package com.specknet.pdiotapp.utils
import android.util.Log
import java.io.File
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date


class FileManager(val extern_dir: File?, var enum: IOutputEnumCompanion) {

    fun getFile(date: Date = Calendar.getInstance().time): File {
        // Initialised intended filename
        val formatter = SimpleDateFormat("yyyy_MM_dd")
        val filename = enum.type()+"_recording_"+formatter.format(date)+".csv"

        Log.d("save", "getFile: Initiliased filename as "+ filename)

        //create fileOut object
        return File(extern_dir, filename)
    }

    fun setupFile() {
        val file = getFile()
        // Creates a new recording file with the correct formatting if it doesn't already exist
        if (file.exists())
            return

        val HEADER = "TIMESTAMP, ID\n"
        file.createNewFile()
        file.appendText(HEADER)
        Log.d("save", "Successfully wrote 1 line to file")
    }

    fun write(action: IOutputEnum) {
        setupFile()

        val file = getFile()

        var row = ""

        val time = Calendar.getInstance().time
        val formatter = SimpleDateFormat("HH:mm:ss")
        val now = formatter.format(time)

        row += now
        row += ","
        row += action.value
        row += "\n"

        if (!file.readLines().last().contains(""+action.value))
            file.appendText(row)

        Log.d("save", "Wrote " + action.toString() + " to file")
    }

    fun parse(date: Date = Calendar.getInstance().time): List<ActivityEntry> {


        val file = getFile(date)

        Log.d("load", "Checking file <" + file.name+">")

        if (!file.exists())
            return emptyList()

        Log.d("load", "Loading file <" + file.name+">")

        val formatter = SimpleDateFormat("HH:mm:ss")
        var st = Calendar.getInstance().time
        var end: Date
        var action: IOutputEnum
        var values: List<String>

        var entries = buildList {

            for (line in file.readLines().drop(1).reversed()) {
                values = line.split(",")
                end = st
                st = formatter.parse(values[0])?:st
                action = enum.parse(values[1])

                if(end.before(st))
                    add(ActivityEntry(action, end, st))
                else
                    add(ActivityEntry(action, st, end))

            }
        }

        return entries
    }

    fun close() {
        enum = Activity
        write(Activity.UNDEFINED)
        enum = Resp
        write(Resp.UNDEFINED)
    }

}