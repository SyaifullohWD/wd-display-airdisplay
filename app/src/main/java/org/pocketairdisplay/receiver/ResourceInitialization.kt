package org.pocketairdisplay.receiver

/** Transfer ownership only after configuration/start succeeds. */
internal inline fun <T> initializeResource(create: () -> T, configure: (T) -> Unit, release: (T) -> Unit): T {
    val resource = create()
    try {
        configure(resource)
        return resource
    } catch (failure: Exception) {
        runCatching { release(resource) }
        throw failure
    }
}
