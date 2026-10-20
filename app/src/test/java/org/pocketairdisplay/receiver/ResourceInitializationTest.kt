package org.pocketairdisplay.receiver

import org.junit.Assert.*
import org.junit.Test

class ResourceInitializationTest {
    private class Resource(var releases: Int = 0)
    @Test fun `failed configuration releases allocated resource`() {
        val resource = Resource()
        val failure = IllegalStateException("configure failed")
        try {
            initializeResource({ resource }, { throw failure }, { it.releases++ })
            fail("expected failure")
        } catch (actual: IllegalStateException) {
            assertSame(failure, actual)
        }
        assertEquals(1, resource.releases)
    }
    @Test fun `failed start preserves original failure even when release throws`() {
        val failure = IllegalStateException("start failed")
        try {
            initializeResource({ Resource() }, { throw failure }, { throw IllegalArgumentException("release failed") })
            fail("expected failure")
        } catch (actual: IllegalStateException) {
            assertSame(failure, actual)
        }
    }
    @Test fun `successful initialization transfers ownership without releasing`() {
        val resource = Resource()
        assertSame(resource, initializeResource({ resource }, {}, { it.releases++ }))
        assertEquals(0, resource.releases)
    }
}
