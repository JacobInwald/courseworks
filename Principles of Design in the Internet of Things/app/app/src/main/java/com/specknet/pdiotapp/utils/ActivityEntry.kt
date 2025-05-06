package com.specknet.pdiotapp.utils


import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date

class ActivityEntry constructor(var action: IOutputEnum, var start: Date,
                                var end: Date
) {


    override fun toString(): String {
        val formatter = SimpleDateFormat("HH:mm:ss")
        return "" + action + " from " + formatter.format(start) + " to " + formatter.format(end)
    }


}