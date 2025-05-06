package com.specknet.pdiotapp.utils

import com.specknet.pdiotapp.R

enum class Resp(override val value: Int, override val type: String = "respiratory"): IOutputEnum {
    UNDEFINED(-1),
    COUGHING(0),
    HYPERVENTILATING(1),
    BREATHING_NORMAL(2),
    SOCIAL_SIGNAL(3);


    override fun toString(): String {
        return when(this) {
            BREATHING_NORMAL -> "Breathing Normally"
            HYPERVENTILATING -> "Hyperventilating"
            COUGHING -> "Coughing"
            SOCIAL_SIGNAL -> "Social Signals"
            UNDEFINED -> "Undefined"
        }
    }

    override fun toStringResource(): Int {
        return when(this){
            BREATHING_NORMAL -> R.string.resp_normal
            HYPERVENTILATING -> R.string.resp_hypervent
            COUGHING -> R.string.resp_cough
            SOCIAL_SIGNAL -> R.string.resp_social
            else -> R.string.activity_undefined
        }
    }

    companion object: IOutputEnumCompanion {
        override fun find(value: Int?): Resp = Resp.values().find { it.value == value }?:UNDEFINED

        override fun type(): String {
            return "respiratory"
        }

        override fun fromOneHot(arr: FloatArray): Resp {
            // arg max function on arg
            val action = arr.withIndex().maxByOrNull { it.value }?.index?:-2
            return find(action.div(2))
        }
        override fun stringList(): List<String> {
            return buildList {
                for (a in Resp.values())
                    add(a.toString())
            }
        }
    }
}