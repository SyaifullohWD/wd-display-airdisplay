package org.pocketairdisplay.receiver

import java.io.File
import org.junit.Assert.*
import org.junit.Test

/** Host backstops; rendered layout and accessibility need device acceptance. */
class BrandingRegressionTest {
    private val root = generateSequence(File(requireNotNull(System.getProperty("user.dir")))) { it.parentFile }
        .first { File(it, "app/src/main/AndroidManifest.xml").exists() }
    private fun read(path: String) = File(root, path).readText()
    private val javaRoot = "app/src/main/java/org/pocketairdisplay/receiver/"

    @Test fun `default identity and launcher use exact new brand without overwriting saved names`() {
        assertEquals("WD Display", WormholeIdentity.DEFAULT_SERVICE_NAME)
        assertEquals("Wormhole Display", WormholeIdentity.sanitizeServiceName("Wormhole Display"))
        assertEquals("Pocket AirDisplay Office", WormholeIdentity.sanitizeServiceName("Pocket AirDisplay Office"))
        assertTrue(read("app/src/main/res/values/strings.xml").contains(">WD Display<"))
        val service = read(javaRoot + "WormholeService.kt")
        assertFalse(service.contains("Pocket AirDisplay"))
        assertTrue(service.contains("R.drawable.ic_wd_monochrome"))
    }
}
