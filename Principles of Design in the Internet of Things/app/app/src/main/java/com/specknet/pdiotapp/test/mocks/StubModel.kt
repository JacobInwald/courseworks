package com.specknet.pdiotapp.mocks

/**
 * A stub model that simulates classification output.
 * Instead of running TFLite, it returns one or more fixed labels.
 */
class StubModel(
    // change list if you want rotating labels
    private val labels: List<String> = listOf("Walking"),
    private val cycleLabels: Boolean = false
) : IModel {

    private var currentIndex = 0

    /**
     * Simulate classification by returning a simple string or array
     * representing an activity label.
     */
    override fun classify(stream: Array<FloatArray>): String {
        val label = labels[currentIndex]

        if (cycleLabels) {
            currentIndex = (currentIndex + 1) % labels.size
        }

        return label
    }
}

