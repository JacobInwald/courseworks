package com.specknet.pdiotapp.utils

import com.specknet.pdiotapp.utils.Activity.ASCENDING
import com.specknet.pdiotapp.utils.Activity.DESCENDING
import com.specknet.pdiotapp.utils.Activity.MISC
import com.specknet.pdiotapp.utils.Activity.RUNNING
import com.specknet.pdiotapp.utils.Activity.SHUFFLE
import com.specknet.pdiotapp.utils.Activity.WALKING

interface IOutputEnum  {

    val value: Int
    val type: String

    override fun toString(): String

    fun toStringResource(): Int

}

interface IOutputEnumCompanion {

    fun find(value: Int?): IOutputEnum

    fun parse(value: String): IOutputEnum = find(value.toInt())

    fun fromOneHot(arr: FloatArray): IOutputEnum

    fun type(): String

    fun stringList(): List<String>
}