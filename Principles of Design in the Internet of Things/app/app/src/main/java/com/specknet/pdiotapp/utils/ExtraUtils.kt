package com.specknet.pdiotapp.utils

class ExtraUtils {

    companion object{

        fun <T> moveLeft(arr: Array<T>, fill: T): Array<T>{
            for (i in 0 until arr.size-1)
                arr[i] = arr[i+1]
            arr[arr.size - 1] = fill

            return arr
        }

    }
}