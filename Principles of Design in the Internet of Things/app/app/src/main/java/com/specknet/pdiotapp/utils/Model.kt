package com.specknet.pdiotapp.utils
import android.util.Log
import org.tensorflow.lite.Interpreter
import kotlin.math.pow
import kotlin.math.sqrt

class Model(val model: Interpreter, val inpDimWidth: Int, val inpDimHeight: Int, val means: List<Double>, val stds: List<Double>) {

    // Stream input is res_x res_y res_z thing_x thing_y thing_z
    fun <T>List<List<T>>.transpose(): List<List<T>> {
        return (this[0].indices).map { i -> (this.indices).map { j -> this[j][i] } }
    }

    fun List<Float>.std(): Double {
        val mean = this.average()
        val variance = this.map { (it - mean).pow(2) }.average()
        return sqrt(variance)
    }

    fun getFeatures(floatArray: Array<FloatArray>): List<Float> {
        // we want mean,stc,min,max of each column of the float array.
        val transpose = floatArray.map { it.asList() }.toList().transpose()
        var dim: List<Float>

        var feature = buildList {
            for (i in (0 until inpDimWidth)) {
                dim = transpose[i]
                add(dim.average().toFloat())
                add(dim.std().toFloat())
                add(dim.minOrNull()?:0f)
                add(dim.maxOrNull()?:0f)
            }

            dim = floatArray.map {sqrt((it[0].pow(2) + it[1].pow(2) + it[2].pow(2)).toDouble()).toFloat() }
            add(dim.average().toFloat())
            add(dim.std().toFloat())
            add(dim.minOrNull()?:0f)
            add(dim.maxOrNull()?:0f)
        }

        return feature
    }


    fun norm(floatArray: Array<FloatArray>): Array<FloatArray> {
        var new = Array(inpDimHeight) { FloatArray(inpDimWidth){0f} }
        for (i in 0 until inpDimHeight) {
            for (j in 0 until inpDimWidth) {
                new[i][j] = ((floatArray[i][j] - means[j]) / stds[j]).toFloat()
            }
        }

        return new
    }


    fun streamToInput(floatArray: Array<FloatArray>): Array<FloatArray> {
        return norm(floatArray).map { it.asList().slice(0 until inpDimWidth).toFloatArray() }.toList().slice(0 until inpDimHeight).toTypedArray()
    }

    fun classify(input: Array<FloatArray>, out: Array<FloatArray>) : Array<FloatArray>{
        /**
         * Runs a model on some given data, pasting it to the output array.
         * @param input Input data of format Array<FloatArray>, the last element of the array will be culled.
         * @param out Output buffer of format FloatBuffer
         * @param model Interpreter class version of a tensorflow model
         * @param type Integer indicating which model is used, 0 -> physical, 1 -> respiratory
         * @return the output buffer
         */

        // Get rid of buffer using dropLast
        Log.d("classify", "classify: Attempting input cleaning")
        val inF = arrayOf(streamToInput(input))

        Log.d("classify", "classify: Running model")

        model.run(inF, out)
        return out
    }

}